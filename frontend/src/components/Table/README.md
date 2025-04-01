# Table Component

## Overview
This is the official table component for the frontend application. It provides a comprehensive set of features for data display, pagination, sorting, and more. Always use this component when implementing tables in the application to ensure consistency.

## Features
- Sortable columns
- Pagination
- Row selection
- Compact, bordered, and striped variants
- Custom cell rendering
- Responsive design

## Usage
```tsx
import Table from 'components/Table/Table';
import 'components/Table/Table.css';

const MyComponent = () => {
  // Data and columns definition
  const data = [...];
  const columns = [...];
  
  return (
    <Table
      data={data}
      columns={columns}
      pagination={{
        pageSize: 10,
        currentPage: 1,
        totalRows: data.length,
        onPageChange: handlePageChange,
        onPageSizeChange: handlePageSizeChange
      }}
      sortable={true}
      onSort={handleSort}
    />
  );
};
```

## Important Guidelines
1. **Do not** create custom table implementations in individual components
2. **Do not** modify the CSS classes directly, use the provided prop options
3. **Do not** comment out portions of the table component
4. If you need additional functionality, extend the Table component properly

## Props
- `data`: Array of data objects to display
- `columns`: Column configuration
- `pagination`: Pagination configuration object
- `sortable`: Enable column sorting
- `className`: Additional CSS classes to apply
- `variant`: Table style variant ('striped', 'bordered', 'compact')
- `selectable`: Enable row selection
- `onRowClick`: Row click handler
- `onSort`: Sort handler function

## CSS Classes
All CSS classes follow the `bms-table` prefix convention:
- `bms-table-container`: Main container
- `bms-table`: Table element
- `bms-table__header`: Header section
- `bms-table__row`: Table row
- `bms-table__cell`: Table cell
- `bms-table__pagination`: Pagination container

See the Table.css file for more detailed styling information. 