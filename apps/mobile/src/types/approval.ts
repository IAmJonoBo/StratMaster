export interface ApprovalStage {
  id: string;
  name: string;
  description: string;
}

export interface ApprovalItem {
  id: string;
  workflow_id: string;
  workflow_name: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  created_at: string;
  due_date?: string;
  author_id: string;
  author_name: string;
  author_avatar_url?: string;
  current_stage: ApprovalStage;
  approvers_required: number;
  approvers_completed: number;
  attachments_count: number;
  comments_count: number;
  tenant_id: string;
}