/**
 * Custom hook for displaying toast notifications.
 */

import { useCallback } from 'react';
import { useSnackbar, VariantType } from 'notistack';

interface UseToastReturn {
  showToast: (message: string, variant?: VariantType) => void;
  showSuccessToast: (message: string) => void;
  showErrorToast: (message: string) => void;
  showWarningToast: (message: string) => void;
  showInfoToast: (message: string) => void;
}

/**
 * Hook for displaying toast notifications
 */
export function useToast(): UseToastReturn {
  const { enqueueSnackbar } = useSnackbar();

  const showToast = useCallback(
    (message: string, variant: VariantType = 'default') => {
      enqueueSnackbar(message, { variant });
    },
    [enqueueSnackbar]
  );

  const showSuccessToast = useCallback(
    (message: string) => {
      showToast(message, 'success');
    },
    [showToast]
  );

  const showErrorToast = useCallback(
    (message: string) => {
      showToast(message, 'error');
    },
    [showToast]
  );

  const showWarningToast = useCallback(
    (message: string) => {
      showToast(message, 'warning');
    },
    [showToast]
  );

  const showInfoToast = useCallback(
    (message: string) => {
      showToast(message, 'info');
    },
    [showToast]
  );

  return {
    showToast,
    showSuccessToast,
    showErrorToast,
    showWarningToast,
    showInfoToast,
  };
}

export default useToast;
