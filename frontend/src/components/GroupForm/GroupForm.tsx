import React from 'react';
import { Modal, Button } from '../../components';
import { BMSPoint } from '../../types/apiTypes';
import './GroupForm.css';

interface GroupFormProps {
  isOpen: boolean;
  onClose: () => void;
  groupName: string;
  groupDescription: string;
  isEditing: boolean;
  selectedPoints: BMSPoint[];
  groupPointsCount?: number;
  onGroupNameChange: (value: string) => void;
  onGroupDescriptionChange: (value: string) => void;
  onSubmit: () => void;
}

/**
 * Form component for creating/editing point groups
 */
const GroupForm: React.FC<GroupFormProps> = ({
  isOpen,
  onClose,
  groupName,
  groupDescription,
  isEditing,
  selectedPoints,
  groupPointsCount = 0,
  onGroupNameChange,
  onGroupDescriptionChange,
  onSubmit
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const isFormValid = groupName.trim() && (isEditing || selectedPoints.length > 0);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Group' : 'Create New Group'}
    >
      <form className="group-form" onSubmit={handleSubmit}>
        <div className="group-form__field">
          <label htmlFor="groupName" className="group-form__label">Group Name</label>
          <input
            id="groupName"
            type="text"
            value={groupName}
            onChange={(e) => onGroupNameChange(e.target.value)}
            className="group-form__input"
            placeholder="Enter group name"
            required
          />
        </div>
        
        <div className="group-form__field">
          <label htmlFor="groupDescription" className="group-form__label">Description</label>
          <textarea
            id="groupDescription"
            value={groupDescription}
            onChange={(e) => onGroupDescriptionChange(e.target.value)}
            className="group-form__textarea"
            placeholder="Enter group description (optional)"
            rows={3}
          />
        </div>
        
        <div className="group-form__info">
          {isEditing ? (
            <div className="group-form__points-count">
              Editing group with {groupPointsCount} point{groupPointsCount !== 1 ? 's' : ''}
            </div>
          ) : (
            <div className="group-form__points-count">
              {selectedPoints.length} point{selectedPoints.length !== 1 ? 's' : ''} will be added to this group
            </div>
          )}
        </div>
        
        <div className="group-form__actions">
          <Button
            type="button"
            onClick={onClose}
            className="group-form__cancel-button"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={!isFormValid}
            className="group-form__submit-button"
          >
            {isEditing ? 'Update Group' : 'Create Group'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default GroupForm;