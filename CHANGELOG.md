# Changelog

## v1.1.0 - Updated GUI and File Handling
- Added safeguard to ignore zero-area rectangles (prevents `ValueError` during extraction).
- Added "Clear Markings" option to remove all drawn rectangles on the current page.
- All JSON files are now saved automatically to the `./regions/` folder.
- Improved console messages for warnings and save confirmations.

## v1.0.0 - Initial Release
- Implemented basic Tkinter-based PDF region selection tool.
- Enabled drawing and saving rectangular coordinates to JSON per page.
- Supported multi-page navigation and rectangle preview.
