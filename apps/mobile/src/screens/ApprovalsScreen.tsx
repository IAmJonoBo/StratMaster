/**
 * Approvals Screen
 * Shows list of pending approvals for the current user
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { format, formatDistanceToNow } from 'date-fns';

import { ApprovalItem } from '../types/approval';
import { ApprovalService } from '../services/ApprovalService';
import { useAuthStore } from '../stores/authStore';
import { RootStackParamList } from '../../App';

type NavigationProp = StackNavigationProp<RootStackParamList>;

const ApprovalsScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const { user } = useAuthStore();
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadApprovals = useCallback(async (isRefresh = false) => {
    try {
      if (!isRefresh) setLoading(true);
      setError(null);

      const pendingApprovals = await ApprovalService.getPendingApprovals();
      setApprovals(pendingApprovals);
    } catch (err) {
      console.error('Failed to load approvals:', err);
      setError('Failed to load approvals. Please try again.');
    } finally {
      setLoading(false);
      if (isRefresh) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadApprovals(true);
  }, [loadApprovals]);

  const handleApprovalPress = (approval: ApprovalItem) => {
    navigation.navigate('ApprovalDetail', { approvalId: approval.id });
  };

  const handleQuickApprove = async (approval: ApprovalItem) => {
    Alert.alert(
      'Quick Approve',
      `Are you sure you want to approve "${approval.title}"?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Approve',
          style: 'default',
          onPress: async () => {
            try {
              await ApprovalService.processApproval(approval.id, 'approve');
              Alert.alert('Success', 'Approval processed successfully');
              loadApprovals();
            } catch (err) {
              console.error('Failed to approve:', err);
              Alert.alert('Error', 'Failed to process approval. Please try again.');
            }
          },
        },
      ]
    );
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '#DC2626';
      case 'high':
        return '#EA580C';
      case 'normal':
        return '#059669';
      case 'low':
        return '#6B7280';
      default:
        return '#6B7280';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'priority-high';
      case 'high':
        return 'keyboard-arrow-up';
      case 'normal':
        return 'remove';
      case 'low':
        return 'keyboard-arrow-down';
      default:
        return 'remove';
    }
  };

  const renderApprovalItem = ({ item }: { item: ApprovalItem }) => {
    const priorityColor = getPriorityColor(item.priority);
    const priorityIcon = getPriorityIcon(item.priority);
    const isOverdue = item.due_date && new Date(item.due_date) < new Date();

    return (
      <TouchableOpacity
        style={[styles.approvalCard, isOverdue && styles.overdueCard]}
        onPress={() => handleApprovalPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.cardHeader}>
          <View style={styles.headerLeft}>
            <Icon
              name={priorityIcon}
              size={20}
              color={priorityColor}
              style={styles.priorityIcon}
            />
            <Text style={styles.workflowName}>{item.workflow_name}</Text>
          </View>
          <TouchableOpacity
            style={[styles.quickApproveButton, { backgroundColor: priorityColor }]}
            onPress={() => handleQuickApprove(item)}
          >
            <Icon name="check" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {item.title}
        </Text>

        <Text style={styles.description} numberOfLines={3}>
          {item.description}
        </Text>

        <View style={styles.metadata}>
          <View style={styles.metadataRow}>
            <Icon name="person" size={16} color="#6B7280" />
            <Text style={styles.metadataText}>{item.author_name}</Text>
          </View>

          <View style={styles.metadataRow}>
            <Icon name="schedule" size={16} color="#6B7280" />
            <Text style={styles.metadataText}>
              {item.due_date 
                ? `Due ${formatDistanceToNow(new Date(item.due_date), { addSuffix: true })}`
                : 'No deadline'
              }
            </Text>
          </View>
        </View>

        <View style={styles.progress}>
          <Text style={styles.progressText}>
            {item.approvers_completed} of {item.approvers_required} approvals
          </Text>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                {
                  width: `${(item.approvers_completed / item.approvers_required) * 100}%`,
                  backgroundColor: priorityColor,
                },
              ]}
            />
          </View>
        </View>

        <View style={styles.tags}>
          <View style={[styles.tag, { backgroundColor: `${priorityColor}20` }]}>
            <Text style={[styles.tagText, { color: priorityColor }]}>
              {item.current_stage.name}
            </Text>
          </View>
          {item.attachments_count > 0 && (
            <View style={styles.tag}>
              <Icon name="attachment" size={12} color="#6B7280" />
              <Text style={styles.tagText}>{item.attachments_count}</Text>
            </View>
          )}
          {item.comments_count > 0 && (
            <View style={styles.tag}>
              <Icon name="comment" size={12} color="#6B7280" />
              <Text style={styles.tagText}>{item.comments_count}</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="check-circle" size={64} color="#6B7280" />
      <Text style={styles.emptyStateTitle}>No Pending Approvals</Text>
      <Text style={styles.emptyStateDescription}>
        You're all caught up! No approvals are waiting for your review.
      </Text>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1E40AF" />
        <Text style={styles.loadingText}>Loading approvals...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="error" size={64} color="#DC2626" />
        <Text style={styles.errorTitle}>Failed to Load Approvals</Text>
        <Text style={styles.errorDescription}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => loadApprovals()}>
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={approvals}
        renderItem={renderApprovalItem}
        keyExtractor={(item) => item.id}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#1E40AF']}
            tintColor="#1E40AF"
          />
        }
        contentContainerStyle={[
          styles.listContainer,
          approvals.length === 0 && styles.emptyContainer,
        ]}
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  listContainer: {
    padding: 16,
  },
  emptyContainer: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 32,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 16,
    textAlign: 'center',
  },
  errorDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#1E40AF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  approvalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  overdueCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#DC2626',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  priorityIcon: {
    marginRight: 8,
  },
  workflowName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    textTransform: 'uppercase',
  },
  quickApproveButton: {
    borderRadius: 16,
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  metadata: {
    marginBottom: 12,
  },
  metadataRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  metadataText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 6,
  },
  progress: {
    marginBottom: 12,
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
    marginBottom: 4,
  },
  tagText: {
    fontSize: 11,
    color: '#6B7280',
    marginLeft: 2,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 16,
  },
  emptyStateDescription: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 32,
  },
});

export default ApprovalsScreen;