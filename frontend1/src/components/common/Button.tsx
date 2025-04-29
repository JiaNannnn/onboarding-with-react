import React from 'react';
import { 
  Button as MuiButton, 
  ButtonProps as MuiButtonProps
} from '@mui/material';

export interface ButtonProps extends MuiButtonProps {
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  loading = false,
  disabled = false,
  ...rest
}) => {
  return (
    <MuiButton
      {...rest}
      disabled={disabled || loading}
    >
      {children}
    </MuiButton>
  );
};

export default Button;
