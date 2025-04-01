import React, { ReactNode, useEffect, useRef, useState } from 'react';
import './Modal.css';

/**
 * Modal component props interface
 */
export interface ModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;
  
  /**
   * Modal title
   */
  title?: string;
  
  /**
   * Modal content
   */
  children: ReactNode;
  
  /**
   * Callback when modal is closed
   */
  onClose: () => void;
  
  /**
   * Whether to close modal when clicking outside
   */
  closeOnOutsideClick?: boolean;
  
  /**
   * Whether to close modal when pressing Escape key
   */
  closeOnEscape?: boolean;
  
  /**
   * Modal size
   */
  size?: 'small' | 'medium' | 'large' | 'full';
  
  /**
   * Custom footer component
   */
  footer?: ReactNode;
  
  /**
   * Show close button in header
   */
  showCloseButton?: boolean;
  
  /**
   * Animation duration in ms
   */
  animationDuration?: number;
  
  /**
   * Custom class name
   */
  className?: string;
  
  /**
   * Whether to show overlay
   */
  showOverlay?: boolean;
  
  /**
   * Custom overlay class name
   */
  overlayClassName?: string;
  
  /**
   * z-index for the modal
   */
  zIndex?: number;
  
  /**
   * Whether to lock scroll when modal is open
   */
  lockScroll?: boolean;
  
  /**
   * Additional header content
   */
  headerContent?: ReactNode;
}

/**
 * Modal component
 * 
 * A flexible and accessible modal dialog component
 */
const Modal: React.FC<ModalProps> = ({
  isOpen,
  title,
  children,
  onClose,
  closeOnOutsideClick = true,
  closeOnEscape = true,
  size = 'medium',
  footer,
  showCloseButton = true,
  animationDuration = 200,
  className = '',
  showOverlay = true,
  overlayClassName = '',
  zIndex = 1000,
  lockScroll = true,
  headerContent,
}) => {
  const [isAnimating, setIsAnimating] = useState<boolean>(false);
  const [isVisible, setIsVisible] = useState<boolean>(isOpen);
  const modalRef = useRef<HTMLDivElement>(null);
  
  // Handle modal opening/closing
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      setIsAnimating(true);
      
      // Lock scroll if enabled
      if (lockScroll) {
        document.body.style.overflow = 'hidden';
      }
      
      // Focus trap
      if (modalRef.current) {
        modalRef.current.focus();
      }
      
      // Animation timing
      const timer = setTimeout(() => {
        setIsAnimating(false);
      }, animationDuration);
      
      return () => clearTimeout(timer);
    } else {
      setIsAnimating(true);
      
      // Animation timing
      const timer = setTimeout(() => {
        setIsVisible(false);
        setIsAnimating(false);
        
        // Restore scroll
        if (lockScroll) {
          document.body.style.overflow = '';
        }
      }, animationDuration);
      
      return () => clearTimeout(timer);
    }
  }, [isOpen, animationDuration, lockScroll]);
  
  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (closeOnEscape && event.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [closeOnEscape, isOpen, onClose]);
  
  // Handle click outside
  const handleOutsideClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (
      closeOnOutsideClick &&
      modalRef.current &&
      event.target instanceof Node &&
      !modalRef.current.contains(event.target)
    ) {
      onClose();
    }
  };
  
  if (!isVisible) {
    return null;
  }
  
  const modalClasses = [
    'bms-modal',
    `bms-modal--${size}`,
    isAnimating ? (isOpen ? 'bms-modal--entering' : 'bms-modal--exiting') : '',
    className,
  ].filter(Boolean).join(' ');
  
  const overlayClasses = [
    'bms-modal-overlay',
    isAnimating ? (isOpen ? 'bms-modal-overlay--entering' : 'bms-modal-overlay--exiting') : '',
    overlayClassName,
  ].filter(Boolean).join(' ');
  
  const modalStyle = {
    animationDuration: `${animationDuration}ms`,
    zIndex,
  };
  
  const overlayStyle = {
    animationDuration: `${animationDuration}ms`,
    zIndex: zIndex - 1,
  };
  
  return (
    <>
      {showOverlay && (
        <div 
          className={overlayClasses}
          style={overlayStyle}
          onClick={closeOnOutsideClick ? onClose : undefined}
        />
      )}
      
      <div
        className="bms-modal-container"
        style={{ zIndex }}
        onClick={handleOutsideClick}
        aria-modal="true"
        role="dialog"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        <div 
          ref={modalRef}
          className={modalClasses}
          style={modalStyle}
          tabIndex={-1}
        >
          {(title || showCloseButton || headerContent) && (
            <div className="bms-modal__header">
              {title && (
                <h2 id="modal-title" className="bms-modal__title">{title}</h2>
              )}
              
              {headerContent && (
                <div className="bms-modal__header-content">
                  {headerContent}
                </div>
              )}
              
              {showCloseButton && (
                <button
                  type="button"
                  className="bms-modal__close-button"
                  aria-label="Close"
                  onClick={onClose}
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              )}
            </div>
          )}
          
          <div className="bms-modal__content">
            {children}
          </div>
          
          {footer && (
            <div className="bms-modal__footer">
              {footer}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Modal; 