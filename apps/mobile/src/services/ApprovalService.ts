import { ApprovalItem } from '../types/approval';

export class ApprovalService {
  static async getPendingApprovals(): Promise<ApprovalItem[]> {
    // Mock data for development
    return [
      {
        id: '1',
        workflow_id: 'wf1',
        workflow_name: 'Strategy Approval',
        title: 'Q4 Marketing Strategy',
        description: 'Review and approve the Q4 marketing strategy for product launch',
        status: 'pending',
        priority: 'high',
        created_at: new Date().toISOString(),
        due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        author_id: 'user1',
        author_name: 'John Doe',
        current_stage: {
          id: 'stage1',
          name: 'Initial Review',
          description: 'Initial stakeholder review'
        },
        approvers_required: 2,
        approvers_completed: 1,
        attachments_count: 3,
        comments_count: 2,
        tenant_id: 'tenant1'
      }
    ];
  }

  static async processApproval(approvalId: string, action: string): Promise<void> {
    // Mock implementation
    console.log(`Processing approval ${approvalId} with action ${action}`);
  }
}