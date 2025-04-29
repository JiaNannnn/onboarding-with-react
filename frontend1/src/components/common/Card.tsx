import React, { ReactNode } from 'react';
import {
  Card as MuiCard,
  CardProps as MuiCardProps,
  CardContent,
  CardHeader,
  CardActions,
  Divider,
  Box,
  Typography,
  IconButton,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

export interface CardProps extends MuiCardProps {
  title?: string;
  subheader?: string;
  action?: ReactNode;
  footer?: ReactNode;
  noPadding?: boolean;
  onRefresh?: () => void;
  loading?: boolean;
  error?: string | null;
  minHeight?: number | string;
  maxHeight?: number | string;
  contentPadding?: number | string;
  className?: string;
  sx?: React.CSSProperties;
}

/**
 * Enhanced Card component with common features like header, refresh, loading state
 */
export const Card: React.FC<CardProps> = ({
  children,
  title,
  subheader,
  action,
  footer,
  noPadding = false,
  onRefresh,
  loading = false,
  error = null,
  minHeight,
  maxHeight,
  contentPadding,
  className,
  sx,
  ...rest
}) => {
  const hasHeader = title || subheader || action || onRefresh;

  return (
    <MuiCard
      {...rest}
      className={className}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: minHeight,
        maxHeight: maxHeight,
        ...(sx as any),
      }}
    >
      {hasHeader && (
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" component="h2">
                {title}
              </Typography>
              {onRefresh && (
                <IconButton onClick={onRefresh} disabled={loading} size="small">
                  <RefreshIcon />
                </IconButton>
              )}
            </Box>
          }
          subheader={subheader}
          action={action}
          sx={{ pb: subheader ? 1 : 0 }}
        />
      )}

      {hasHeader && <Divider />}

      <CardContent
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          p: noPadding ? 0 : contentPadding,
          ...(contentPadding === 0 && { '&:last-child': { pb: 0 } }),
        }}
      >
        {children}
      </CardContent>

      {footer && (
        <>
          <Divider />
          <CardActions>{footer}</CardActions>
        </>
      )}
    </MuiCard>
  );
};

export default Card;
