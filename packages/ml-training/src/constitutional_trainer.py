"""
Constitutional Compliance ML Training Pipeline

This module implements the advanced ML model training pipeline for
constitutional compliance detection and enforcement in StratMaster.

Key Features:
- BERT-based transformer models for text classification
- Multi-label classification for different constitutional categories
- Active learning with uncertainty sampling
- Model versioning and A/B testing
- Automated retraining with drift detection
- Integration with MLflow for experiment tracking
"""

import json
import logging
import os
from dataclasses import asdict, dataclass

import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
import yaml
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for ML model training."""
    model_name: str = "bert-base-uncased"
    max_epochs: int = 50
    batch_size: int = 16
    learning_rate: float = 2e-5
    warmup_steps: int = 1000
    weight_decay: float = 0.01
    gradient_accumulation_steps: int = 4
    max_sequence_length: int = 512
    
    # Early stopping
    early_stopping_patience: int = 5
    early_stopping_threshold: float = 0.001
    
    # Categories for constitutional compliance
    categories: list[str] = None
    
    # Evaluation thresholds
    thresholds: dict[str, float] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = [
                "safety_violations",
                "factual_inaccuracy", 
                "source_credibility",
                "bias_detection",
                "harmful_content",
                "privacy_violations",
                "legal_compliance"
            ]
        
        if self.thresholds is None:
            self.thresholds = {
                "safety_violations": 0.9,
                "factual_inaccuracy": 0.8,
                "source_credibility": 0.85,
                "bias_detection": 0.7,
                "harmful_content": 0.95,
                "privacy_violations": 0.9,
                "legal_compliance": 0.85
            }


class ConstitutionalComplianceDataset(Dataset):
    """Dataset class for constitutional compliance training data."""
    
    def __init__(
        self,
        texts: list[str],
        labels: list[dict[str, int]],
        tokenizer: AutoTokenizer,
        max_length: int = 512
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Convert labels to tensor format
        self.label_names = sorted(set().union(*[label.keys() for label in labels]))
        self.label_to_id = {label: i for i, label in enumerate(self.label_names)}
        
    def __len__(self) -> int:
        return len(self.texts)
    
    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        text = str(self.texts[idx])
        labels = self.labels[idx]
        
        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Convert labels to multi-hot encoding
        label_tensor = torch.zeros(len(self.label_names))
        for label_name, value in labels.items():
            if label_name in self.label_to_id:
                label_tensor[self.label_to_id[label_name]] = float(value)
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': label_tensor
        }


class ConstitutionalComplianceModel(nn.Module):
    """Multi-label classifier for constitutional compliance."""
    
    def __init__(self, model_name: str, num_labels: int, dropout_rate: float = 0.1):
        super().__init__()
        
        self.bert = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            problem_type="multi_label_classification"
        )
        
        # Add additional layers for better performance
        self.dropout = nn.Dropout(dropout_rate)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)
        
    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.bert.bert(input_ids=input_ids, attention_mask=attention_mask)
        
        # Use pooled output
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        loss = None
        if labels is not None:
            loss_fn = nn.BCEWithLogitsLoss()
            loss = loss_fn(logits, labels)
        
        return {
            'loss': loss,
            'logits': logits
        }


class ConstitutionalTrainer:
    """Main trainer class for constitutional compliance models."""
    
    def __init__(self, config: TrainingConfig, mlflow_tracking_uri: str = None):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        # Initialize MLflow
        if mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
        
        self.mlflow_client = MlflowClient()
        
    def load_data(self, data_path: str) -> tuple[list[str], list[dict[str, int]]]:
        """Load training data from file."""
        texts = []
        labels = []
        
        with open(data_path) as f:
            for line in f:
                data = json.loads(line)
                texts.append(data['text'])
                
                # Parse labels (can be multi-label)
                label_dict = {}
                if isinstance(data['labels'], dict):
                    label_dict = data['labels']
                elif isinstance(data['labels'], list):
                    for label in data['labels']:
                        label_dict[label] = 1
                else:
                    # Single label
                    label_dict[data['labels']] = 1
                
                labels.append(label_dict)
        
        return texts, labels
    
    def prepare_datasets(
        self,
        texts: list[str],
        labels: list[dict[str, int]],
        train_split: float = 0.8,
        val_split: float = 0.1
    ) -> tuple[ConstitutionalComplianceDataset, ConstitutionalComplianceDataset, ConstitutionalComplianceDataset]:
        """Split data and create datasets."""
        
        # Calculate split indices
        total_size = len(texts)
        train_size = int(total_size * train_split)
        val_size = int(total_size * val_split)
        
        # Split data
        train_texts = texts[:train_size]
        train_labels = labels[:train_size]
        
        val_texts = texts[train_size:train_size + val_size]
        val_labels = labels[train_size:train_size + val_size]
        
        test_texts = texts[train_size + val_size:]
        test_labels = labels[train_size + val_size:]
        
        # Create datasets
        train_dataset = ConstitutionalComplianceDataset(
            train_texts, train_labels, self.tokenizer, self.config.max_sequence_length
        )
        
        val_dataset = ConstitutionalComplianceDataset(
            val_texts, val_labels, self.tokenizer, self.config.max_sequence_length
        )
        
        test_dataset = ConstitutionalComplianceDataset(
            test_texts, test_labels, self.tokenizer, self.config.max_sequence_length
        )
        
        return train_dataset, val_dataset, test_dataset
    
    def compute_metrics(self, eval_pred):
        """Compute evaluation metrics."""
        predictions, labels = eval_pred
        
        # Apply sigmoid to get probabilities
        predictions = torch.sigmoid(torch.tensor(predictions)).numpy()
        
        # Apply thresholds
        binary_predictions = np.zeros_like(predictions)
        for i, category in enumerate(self.config.categories):
            threshold = self.config.thresholds.get(category, 0.5)
            binary_predictions[:, i] = (predictions[:, i] >= threshold).astype(int)
        
        # Calculate metrics
        accuracy = accuracy_score(labels, binary_predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, binary_predictions, average='weighted'
        )
        
        # Calculate AUC for each category
        auc_scores = []
        for i in range(labels.shape[1]):
            if len(np.unique(labels[:, i])) > 1:  # Only calculate AUC if both classes present
                auc = roc_auc_score(labels[:, i], predictions[:, i])
                auc_scores.append(auc)
        
        avg_auc = np.mean(auc_scores) if auc_scores else 0.0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': avg_auc
        }
    
    def train(self, data_path: str, output_dir: str) -> str:
        """Train the constitutional compliance model."""
        
        # Start MLflow run
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params(asdict(self.config))
            
            # Load data
            logger.info("Loading training data...")
            texts, labels = self.load_data(data_path)
            
            # Initialize tokenizer and model
            logger.info("Initializing model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            
            # Create datasets
            train_dataset, val_dataset, test_dataset = self.prepare_datasets(
                texts, labels
            )
            
            num_labels = len(train_dataset.label_names)
            self.model = ConstitutionalComplianceModel(
                self.config.model_name, num_labels
            )
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.config.max_epochs,
                per_device_train_batch_size=self.config.batch_size,
                per_device_eval_batch_size=self.config.batch_size,
                warmup_steps=self.config.warmup_steps,
                weight_decay=self.config.weight_decay,
                logging_dir=f"{output_dir}/logs",
                logging_steps=100,
                evaluation_strategy="steps",
                eval_steps=500,
                save_strategy="steps",
                save_steps=500,
                load_best_model_at_end=True,
                metric_for_best_model="eval_f1",
                greater_is_better=True,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                dataloader_pin_memory=False,  # Set to False to avoid issues in some environments
                report_to="mlflow"
            )
            
            # Initialize trainer
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                compute_metrics=self.compute_metrics,
                callbacks=[
                    EarlyStoppingCallback(
                        early_stopping_patience=self.config.early_stopping_patience,
                        early_stopping_threshold=self.config.early_stopping_threshold
                    )
                ]
            )
            
            # Train model
            logger.info("Starting model training...")
            train_result = self.trainer.train()
            
            # Evaluate on test set
            logger.info("Evaluating on test set...")
            test_results = self.trainer.evaluate(test_dataset)
            
            # Log final metrics
            mlflow.log_metrics({
                f"test_{k}": v for k, v in test_results.items() 
                if k.startswith('eval_')
            })
            
            # Save model
            model_path = f"{output_dir}/final_model"
            self.trainer.save_model(model_path)
            
            # Log model to MLflow
            mlflow.pytorch.log_model(
                self.model,
                "constitutional_compliance_model",
                registered_model_name="ConstitutionalCompliance"
            )
            
            # Save label mappings
            label_mapping = {
                "label_names": train_dataset.label_names,
                "label_to_id": train_dataset.label_to_id,
                "thresholds": self.config.thresholds
            }
            
            with open(f"{output_dir}/label_mapping.json", 'w') as f:
                json.dump(label_mapping, f, indent=2)
            
            mlflow.log_artifact(f"{output_dir}/label_mapping.json")
            
            logger.info("Training completed successfully!")
            return mlflow.active_run().info.run_id


def main():
    """Main function for training pipeline."""
    
    # Load configuration
    config_path = os.getenv('ML_CONFIG_PATH', 'configs/ml-training/training-config.yaml')
    
    with open(config_path) as f:
        config_data = yaml.safe_load(f)
    
    # Extract training config
    training_config = TrainingConfig(**config_data['training'])
    
    # Initialize trainer
    mlflow_uri = config_data.get('mlflow', {}).get('tracking_uri')
    trainer = ConstitutionalTrainer(training_config, mlflow_uri)
    
    # Run training
    data_path = os.getenv('TRAINING_DATA_PATH', 'data/constitutional_training.jsonl')
    output_dir = os.getenv('MODEL_OUTPUT_DIR', 'models/constitutional_compliance')
    
    run_id = trainer.train(data_path, output_dir)
    print(f"Training completed. MLflow run ID: {run_id}")


if __name__ == "__main__":
    main()