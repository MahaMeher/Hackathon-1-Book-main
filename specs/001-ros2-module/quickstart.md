# Quickstart Guide: ROS 2 Book Development

## Prerequisites
- Node.js 18 or higher
- npm or yarn package manager
- Git for version control

## Setup Instructions

1. **Install Docusaurus**
   ```bash
   npx create-docusaurus@latest website classic
   ```

2. **Navigate to project directory**
   ```bash
   cd website
   ```

3. **Start development server**
   ```bash
   npm start
   ```
   This command starts a local development server and opens the website in your browser. Most changes are reflected live without restarting the server.

4. **Create the Module 1 structure**
   ```bash
   mkdir -p docs/module1
   ```

5. **Create the three chapters for Module 1**
   ```bash
   touch docs/module1/chapter1-ros2-fundamentals.md
   touch docs/module1/chapter2-ros2-communication.md
   touch docs/module1/chapter3-urdf-humanoids.md
   ```

## Basic Content Structure

Each chapter file should follow this basic MDX structure:

```mdx
---
title: Chapter Title
sidebar_position: 1
description: Brief description of the chapter content
---

# Chapter Title

Content goes here...

## Section Heading

More content...

### Subsection

Detailed information...
```

## Configuration Files

1. **Update `docusaurus.config.js`** with site metadata
2. **Update `sidebars.js`** to include the new module and chapters in navigation

## Building for Production

```bash
npm run build
```

This generates static content into the `build` directory and can be served using any static hosting service.

## Deployment to GitHub Pages

1. Configure the deployment settings in `docusaurus.config.js`
2. Run the build command
3. The site can be deployed to GitHub Pages following Docusaurus documentation