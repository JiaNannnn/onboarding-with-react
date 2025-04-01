import { useState } from 'react';
import { BMSPoint } from '../../types/apiTypes';

interface GroupFormState {
  groupName: string;
  groupDescription: string;
  groupToEdit: string | null;
}

/**
 * Hook for managing point group operations
 */
export function useGroupManagement() {
  // State for group management
  const [showGroupModal, setShowGroupModal] = useState<boolean>(false);
  const [showConfirmDeleteGroup, setShowConfirmDeleteGroup] = useState<boolean>(false);
  const [groupToDelete, setGroupToDelete] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [draggedGroupId, setDraggedGroupId] = useState<string | null>(null);
  const [draggedPointId, setDraggedPointId] = useState<string | null>(null);
  const [selectedPoints, setSelectedPoints] = useState<BMSPoint[]>([]);
  
  // Group form state
  const [groupForm, setGroupForm] = useState<GroupFormState>({
    groupName: '',
    groupDescription: '',
    groupToEdit: null
  });

  // Toggle expand/collapse group
  const toggleGroupExpand = (groupId: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
  };

  // Handle point selection
  const handlePointSelect = (point: BMSPoint) => {
    setSelectedPoints(prev => {
      const isAlreadySelected = prev.some(p => p.id === point.id);
      if (isAlreadySelected) {
        return prev.filter(p => p.id !== point.id);
      } else {
        return [...prev, point];
      }
    });
  };

  // Handle multiple point selection
  const handleSelectPoints = (points: BMSPoint[]) => {
    setSelectedPoints(points);
  };

  // Clear selected points
  const clearSelectedPoints = () => {
    setSelectedPoints([]);
  };

  // Open create group modal
  const openCreateGroupModal = () => {
    setGroupForm({
      groupName: '',
      groupDescription: '',
      groupToEdit: null
    });
    setShowGroupModal(true);
  };

  // Open edit group modal
  const openEditGroupModal = (groupId: string, groupName: string, groupDescription: string) => {
    setGroupForm({
      groupName,
      groupDescription,
      groupToEdit: groupId
    });
    setShowGroupModal(true);
  };

  // Close group modal
  const closeGroupModal = () => {
    setShowGroupModal(false);
    setGroupForm({
      groupName: '',
      groupDescription: '',
      groupToEdit: null
    });
  };

  // Update group form field
  const updateGroupForm = (field: keyof GroupFormState, value: string) => {
    setGroupForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Open delete group confirmation
  const confirmDeleteGroup = (groupId: string) => {
    setGroupToDelete(groupId);
    setShowConfirmDeleteGroup(true);
  };

  // Open delete all groups confirmation
  const confirmDeleteAllGroups = () => {
    setGroupToDelete(null);
    setShowConfirmDeleteGroup(true);
  };

  // Cancel group deletion
  const cancelDeleteGroup = () => {
    setShowConfirmDeleteGroup(false);
    setGroupToDelete(null);
  };

  // Handle drag start for point
  const handlePointDragStart = (e: React.DragEvent, pointId: string) => {
    e.dataTransfer.setData('pointId', pointId);
    setDraggedPointId(pointId);
    e.dataTransfer.effectAllowed = 'move';
  };
  
  // Handle drag over for group
  const handleGroupDragOver = (e: React.DragEvent, groupId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };
  
  // Handle drag start for group
  const handleGroupDragStart = (e: React.DragEvent, groupId: string) => {
    e.dataTransfer.setData('groupId', groupId);
    setDraggedGroupId(groupId);
    e.dataTransfer.effectAllowed = 'move';
  };

  return {
    // State
    showGroupModal,
    showConfirmDeleteGroup,
    groupToDelete,
    expandedGroups,
    draggedGroupId,
    draggedPointId,
    selectedPoints,
    groupForm,
    
    // Actions
    toggleGroupExpand,
    handlePointSelect,
    handleSelectPoints,
    clearSelectedPoints,
    openCreateGroupModal,
    openEditGroupModal,
    closeGroupModal,
    updateGroupForm,
    confirmDeleteGroup,
    confirmDeleteAllGroups,
    cancelDeleteGroup,
    handlePointDragStart,
    handleGroupDragOver,
    handleGroupDragStart,
    setDraggedPointId,
    setDraggedGroupId
  };
}