import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardActions, 
  Button,
  Paper,
  Divider,
} from '@mui/material';
import { 
  CloudDownload as FetchIcon, 
  GroupWork as GroupIcon, 
  AccountTree as MappingIcon, 
  Save as SavedIcon 
} from '@mui/icons-material';
import { useAppContext } from '../store/AppContext';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { state } = useAppContext();
  const { points, groups, mappings } = state;

  const cards = [
    {
      title: 'Fetch Points',
      description: 'Fetch and manage building automation system points from various sources.',
      icon: <FetchIcon sx={{ fontSize: 40 }} />,
      stats: `${points.length} points available`,
      action: () => navigate('/fetch-points'),
      buttonText: 'Fetch Points'
    },
    {
      title: 'Group Points',
      description: 'Create and manage logical groups of related points for easier mapping.',
      icon: <GroupIcon sx={{ fontSize: 40 }} />,
      stats: `${groups.length} groups created`,
      action: () => navigate('/group-points'),
      buttonText: 'Manage Groups'
    },
    {
      title: 'Mapping Points',
      description: 'Map points between different building automation systems or standards.',
      icon: <MappingIcon sx={{ fontSize: 40 }} />,
      stats: 'Create and edit mappings',
      action: () => navigate('/mapping-points'),
      buttonText: 'Map Points'
    },
    {
      title: 'Saved Mappings',
      description: 'View and manage your saved point mappings and export them for use.',
      icon: <SavedIcon sx={{ fontSize: 40 }} />,
      stats: `${mappings.length} mappings saved`,
      action: () => navigate('/saved-mappings'),
      buttonText: 'View Mappings'
    }
  ];

  return (
    <Box>
      <Paper elevation={0} sx={{ p: 3, mb: 4, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          BMS Points Mapping Tool
        </Typography>
        <Typography variant="body1" color="textSecondary">
          This application helps you map building automation system points between different systems,
          standards, and naming conventions.
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        {cards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mb: 2,
                    color: 'primary.main'
                  }}
                >
                  {card.icon}
                  <Typography variant="h6" component="h2" sx={{ ml: 1 }}>
                    {card.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="textSecondary" paragraph>
                  {card.description}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2" color="primary" fontWeight="medium">
                  {card.stats}
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  fullWidth 
                  variant="outlined" 
                  onClick={card.action}
                >
                  {card.buttonText}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Dashboard;