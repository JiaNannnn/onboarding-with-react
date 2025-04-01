import React from 'react';
import { Modal, Button } from '../../components';
import { PointGroup } from '../../types/apiTypes';
import './DeleteConfirmation.css';

interface DeleteConfirmationProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  groupToDelete: string | null;
  groups: Record<string, PointGroup>;
}

/**
 * Confirmation dialog for deleting groups
 */
const DeleteConfirmation: React.FC<DeleteConfirmationProps> = ({
  isOpen,
  onClose,
  onConfirm,
  groupToDelete,
  groups
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirm Delete"
    >
      <div className="delete-confirmation">
        <p className="delete-confirmation__message">
          {groupToDelete ? (
            `Are you sure you want to delete the group "${groups[groupToDelete]?.name}"?`
          ) : (
            'Are you sure you want to delete all groups?'
          )}
        </p>
        <p className="delete-confirmation__warning">
          This action cannot be undone. Points will be returned to the ungrouped pool.
        </p>
        
        <div className="delete-confirmation__actions">
          <Button
            onClick={onClose}
            className="delete-confirmation__cancel-button"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            className="delete-confirmation__confirm-button"
          >
            {groupToDelete ? 'Delete Group' : 'Delete All Groups'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default DeleteConfirmation;