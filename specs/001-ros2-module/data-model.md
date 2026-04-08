# Data Model: ROS 2 Book Content Structure

## Content Entities

### Module
- **Name**: String (required) - The module identifier (e.g., "module1")
- **Title**: String (required) - The display title (e.g., "The Robotic Nervous System")
- **Description**: String (optional) - Brief overview of the module
- **Chapters**: Array of Chapter entities - Ordered list of chapters in the module
- **Navigation**: Object - Sidebar configuration for the module

### Chapter
- **ID**: String (required) - Unique identifier for the chapter
- **Title**: String (required) - Display title of the chapter
- **Content**: String (required) - The MDX content of the chapter
- **Prev/Next**: String (optional) - Navigation links to adjacent chapters
- **Metadata**: Object - Additional metadata (author, date, difficulty, etc.)

### ContentSection
- **Type**: String (required) - Type of content (text, code, diagram, exercise)
- **Content**: String (required) - The actual content
- **Attributes**: Object (optional) - Additional attributes for the section

## Relationships
- Module contains multiple Chapters (1 to many)
- Chapter contains multiple ContentSections (1 to many)

## Validation Rules
- Module ID must be unique across all modules
- Chapter ID must be unique within a module
- Chapter titles must not exceed 100 characters
- Module descriptions should be between 20-200 characters
- All content must be properly formatted MDX

## State Transitions
- Draft → Review → Published (content workflow)
- Each chapter can be in a different state independently
- Module state is determined by the highest state of its chapters