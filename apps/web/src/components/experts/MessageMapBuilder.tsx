'use client'

import { useState } from 'react'
import { MessageMapNode } from '@/types/experts'
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'

const sampleMessageMap: MessageMapNode[] = [
  {
    id: 'core-1',
    type: 'core',
    content: 'Revolutionary product launch',
    level: 0,
    children: ['support-1', 'support-2']
  },
  {
    id: 'support-1',
    type: 'supporting',
    content: 'Breakthrough technology',
    level: 1,
    parent_id: 'core-1',
    children: ['proof-1']
  },
  {
    id: 'support-2',
    type: 'supporting',
    content: 'Guaranteed results',
    level: 1,
    parent_id: 'core-1',
    children: ['proof-2']
  },
  {
    id: 'proof-1',
    type: 'proof',
    content: 'Scientific research backing',
    level: 2,
    parent_id: 'support-1',
    children: []
  },
  {
    id: 'proof-2',
    type: 'proof',
    content: 'Customer testimonials',
    level: 2,
    parent_id: 'support-2',
    children: []
  }
]

export function MessageMapBuilder() {
  const [messageMap, setMessageMap] = useState<MessageMapNode[]>(sampleMessageMap)
  const [editingNode, setEditingNode] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'core':
        return 'bg-blue-100 border-blue-300 text-blue-900'
      case 'supporting':
        return 'bg-green-100 border-green-300 text-green-900'
      case 'proof':
        return 'bg-purple-100 border-purple-300 text-purple-900'
      default:
        return 'bg-gray-100 border-gray-300 text-gray-900'
    }
  }

  const startEditing = (node: MessageMapNode) => {
    setEditingNode(node.id)
    setEditContent(node.content)
  }

  const saveEdit = () => {
    if (editingNode) {
      setMessageMap(prev => prev.map(node => 
        node.id === editingNode 
          ? { ...node, content: editContent }
          : node
      ))
      setEditingNode(null)
      setEditContent('')
    }
  }

  const cancelEdit = () => {
    setEditingNode(null)
    setEditContent('')
  }

  const addNode = (parentId: string, type: 'supporting' | 'proof') => {
    const parent = messageMap.find(n => n.id === parentId)
    if (!parent) return

    const newId = `${type}-${Date.now()}`
    const newNode: MessageMapNode = {
      id: newId,
      type,
      content: `New ${type} message`,
      level: parent.level + 1,
      parent_id: parentId,
      children: []
    }

    setMessageMap(prev => [
      ...prev.map(node => 
        node.id === parentId 
          ? { ...node, children: [...node.children, newId] }
          : node
      ),
      newNode
    ])
  }

  const removeNode = (nodeId: string) => {
    const node = messageMap.find(n => n.id === nodeId)
    if (!node || node.type === 'core') return // Don't allow removing core message

    setMessageMap(prev => prev
      .filter(n => n.id !== nodeId && !isDescendant(n.id, nodeId, prev))
      .map(n => n.parent_id === node.parent_id 
        ? { ...n, children: n.children.filter(id => id !== nodeId) }
        : n
      )
    )
  }

  const isDescendant = (nodeId: string, ancestorId: string, nodes: MessageMapNode[]): boolean => {
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return false
    if (node.parent_id === ancestorId) return true
    if (node.parent_id) return isDescendant(node.parent_id, ancestorId, nodes)
    return false
  }

  const renderNode = (node: MessageMapNode, depth = 0) => {
    const isEditing = editingNode === node.id
    const children = messageMap.filter(n => n.parent_id === node.id)

    return (
      <div key={node.id} className="space-y-2">
        <div 
          className={`message-node ${getNodeColor(node.type)} relative`}
          style={{ marginLeft: `${depth * 1.5}rem` }}
        >
          {/* Connector line */}
          {depth > 0 && (
            <div 
              className="message-connector top-0"
              style={{ top: '-1rem' }}
            />
          )}

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs font-medium uppercase tracking-wide opacity-75">
                  {node.type}
                </span>
                {node.type !== 'core' && (
                  <button
                    onClick={() => removeNode(node.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                )}
              </div>
              
              {isEditing ? (
                <div className="space-y-2">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full p-2 text-sm border border-gray-300 rounded resize-none"
                    rows={2}
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={saveEdit}
                      className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="px-2 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  onClick={() => startEditing(node)}
                  className="cursor-pointer hover:bg-black hover:bg-opacity-5 p-1 rounded"
                >
                  {node.content}
                </div>
              )}
            </div>
          </div>

          {/* Add child buttons */}
          {!isEditing && node.type !== 'proof' && (
            <div className="flex space-x-1 mt-2">
              <button
                onClick={() => addNode(node.id, node.type === 'core' ? 'supporting' : 'proof')}
                className="flex items-center space-x-1 px-2 py-1 text-xs bg-white bg-opacity-50 border border-current rounded hover:bg-opacity-75"
              >
                <PlusIcon className="h-3 w-3" />
                <span>{node.type === 'core' ? 'Support' : 'Proof'}</span>
              </button>
            </div>
          )}
        </div>

        {/* Render children */}
        {children.map(child => renderNode(child, depth + 1))}
      </div>
    )
  }

  const coreNodes = messageMap.filter(n => n.type === 'core')

  return (
    <div className="message-map">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h3 className="font-medium text-gray-900">Message Structure</h3>
        <p className="text-sm text-gray-600 mt-1">
          Build your message hierarchy with core message, supporting points, and proof elements
        </p>
      </div>
      
      <div className="p-4 space-y-4">
        {coreNodes.map(node => renderNode(node))}
        
        {coreNodes.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p className="mb-4">No message map created yet</p>
            <button
              onClick={() => {
                const coreNode: MessageMapNode = {
                  id: 'core-1',
                  type: 'core',
                  content: 'Your core message',
                  level: 0,
                  children: []
                }
                setMessageMap([coreNode])
              }}
              className="px-4 py-2 bg-stratmaster-primary text-white rounded-lg hover:bg-blue-700"
            >
              Create Message Map
            </button>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded bg-blue-100 border border-blue-300"></div>
            <span>Core Message</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded bg-green-100 border border-green-300"></div>
            <span>Supporting Point</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></div>
            <span>Proof Element</span>
          </div>
        </div>
      </div>
    </div>
  )
}