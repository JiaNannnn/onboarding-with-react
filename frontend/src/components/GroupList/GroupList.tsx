import React from 'react';
import { Button } from '../../components';
import { BMSPoint, PointGroup } from '../../types/apiTypes';
import './GroupList.css';

interface GroupListProps {
  groups: Record<string, PointGroup>;
  expandedGroups: Record<string, boolean>;
  draggedGroupId: string | null;
  isLoading: boolean;
  onToggleExpand: (groupId: string) => void;
  onEditGroup: (groupId: string) => void;
  onDeleteGroup: (groupId: string) => void;
  onDeleteAllGroups: () => void;
  onRemovePointFromGroup: (groupId: string, pointId: string) => void;
  onGroupDragStart: (e: React.DragEvent, groupId: string) => void;
  onGroupDragOver: (e: React.DragEvent, groupId: string) => void;
  onGroupDrop: (e: React.DragEvent, groupId: string) => void;
}

/**
 * Component for displaying and managing groups
 */
const GroupList: React.FC<GroupListProps> = ({
  groups,
  expandedGroups,
  draggedGroupId,
  isLoading,
  onToggleExpand,
  onEditGroup,
  onDeleteGroup,
  onDeleteAllGroups,
  onRemovePointFromGroup,
  onGroupDragStart,
  onGroupDragOver,
  onGroupDrop
}) => {
  const groupEntries = Object.entries(groups);
  
  // If no groups, show empty state
  if (groupEntries.length === 0) {
    return (
      <div className="group-list__empty">
        <p>No groups created yet.</p>
        <p>Create groups manually by selecting points and clicking "Create Group", or use AI-assisted grouping.</p>
      </div>
    );
  }
  
  // If loading, show loading state
  if (isLoading) {
    return (
      <div className="group-list__loading">
        Loading groups...
      </div>
    );
  }

  return (
    <div className="group-list">
      <div className="group-list__items">
        {groupEntries.map(([groupId, group]) => (
          <div 
            key={groupId}
            className={`group-list__item ${draggedGroupId === groupId ? 'group-list__item--dragging' : ''}`}
            draggable
            onDragStart={(e) => onGroupDragStart(e, groupId)}
            onDragOver={(e) => onGroupDragOver(e, groupId)}
            onDrop={(e) => onGroupDrop(e, groupId)}
          >
            <div className="group-list__header">
              <button 
                className="group-list__expand-button"
                onClick={() => onToggleExpand(groupId)}
                aria-label={expandedGroups[groupId] ? 'Collapse group' : 'Expand group'}
              >
                {expandedGroups[groupId] ? '▾' : '▸'}
              </button>
              
              <h3 className="group-list__name">{group.name}</h3>
              
              <div className="group-list__count">
                {group.points.length} point{group.points.length !== 1 ? 's' : ''}
              </div>
              
              <div className="group-list__actions">
                <button
                  className="group-list__edit-button"
                  onClick={() => onEditGroup(groupId)}
                  title="Edit group"
                >
                  Edit
                </button>
                <button
                  className="group-list__delete-button"
                  onClick={() => onDeleteGroup(groupId)}
                  title="Delete group"
                >
                  Delete
                </button>
              </div>
            </div>
            
            {expandedGroups[groupId] && (
              <div className="group-list__details">
                {group.description && (
                  <div className="group-list__description">
                    {group.description}
                  </div>
                )}
                
                <div className="group-list__points-container">
                  <h4 className="group-list__points-title">Points</h4>
                  <ul className="group-list__points">
                    {group.points.map((point: BMSPoint) => (
                      <li key={point.id} className="group-list__point">
                        <span className="group-list__point-name">{point.pointName}</span>
                        <span className="group-list__point-type">{point.pointType}</span>
                        <button
                          className="group-list__remove-point"
                          onClick={() => onRemovePointFromGroup(groupId, point.id)}
                          title="Remove point from group"
                        >
                          &times;
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {groupEntries.length > 0 && (
        <div className="group-list__footer">
          <Button 
            onClick={onDeleteAllGroups}
            className="group-list__clear-all"
          >
            Clear All Groups
          </Button>
        </div>
      )}
    </div>
  );
};

export default GroupList;