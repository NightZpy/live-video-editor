# Manual Cut Editing Feature

## Overview
The video preview component now supports manual editing of cut start and end times through an intuitive user interface.

## Features Implemented

### 1. Editable Time Fields
- **Activation**: Double-click on start time or end time labels to enter edit mode.
- **Visual Feedback**: Fields change to entry boxes with distinct styling when editing.
- **Cancel**: Press `Escape` to cancel editing and revert to original values.

### 2. Save Mechanisms
- **Enter Key**: Press `Enter` to save changes.
- **Click Outside**: Clicking outside the entry field automatically saves changes.
- **Save Button**: Click the "Save" button to apply changes.
- **Reset Button**: Click the "Reset" button to revert to original values.

### 3. Validation
- **Time Format**: Validates HH:MM:SS format.
- **Logical Order**: Ensures start time is before end time.
- **Video Duration**: Prevents end time from exceeding video duration.
- **Error Handling**: Shows appropriate error messages for invalid inputs.

### 4. Data Propagation
- **Real-time Updates**: Changes are immediately reflected in the video preview.
- **Cuts List Sync**: Modified cuts are updated in the cuts list component.
- **Cache Update**: Changes are persisted to the cache file.
- **Visual Refresh**: Video preview updates to show the new cut boundaries.

## User Interface

### Visual States
- **Normal State**: Time labels displayed as read-only text.
- **Edit State**: Time labels replaced with entry fields.
- **Validation Error**: Red border indicates invalid input.

### Controls
- **Start Time Field**: Editable start time in HH:MM:SS format.
- **End Time Field**: Editable end time in HH:MM:SS format.
- **Save Button**: Applies current changes.
- **Reset Button**: Reverts to original values.

## Technical Implementation

### Key Components
- `start_edit_time()`: Initiates editing mode for time fields.
- `save_time_edit()`: Validates and saves time changes.
- `cancel_time_edit()`: Cancels editing and restores original values.
- `validate_current_edit()`: Performs comprehensive validation.
- `notify_cut_data_changed()`: Propagates changes to other components.

### State Management
- `original_cut_data`: Stores original cut data for reset functionality.
- `is_editing_cut`: Tracks editing state.
- `editing_start_time`/`editing_end_time`: Track which fields are being edited.

### Event Handling
- **Double-click**: Activates edit mode.
- **Key bindings**: Enter (save), Escape (cancel).
- **Focus events**: FocusOut triggers automatic save.

## Usage Examples

1. **Edit Start Time**:
   - Double-click on the start time (e.g., "00:00:14").
   - Type new time (e.g., "00:00:10").
   - Press Enter or click outside to save.

2. **Edit End Time**:
   - Double-click on the end time (e.g., "00:01:23").
   - Type new time (e.g., "00:01:30").
   - Press Enter or click outside to save.

3. **Reset Changes**:
   - Make edits to start/end times.
   - Click the "Reset" button to revert to original values.

4. **Batch Edit**:
   - Edit start time, then edit end time.
   - Click the "Save" button to apply both changes simultaneously.

## Error Handling

The system provides comprehensive error handling for:
- Invalid time formats (non-numeric, incorrect format).
- Logical errors (start >= end).
- Duration constraints (end > video duration).
- Empty or malformed input.

All errors are displayed to the user with clear, actionable messages.
