# TechFlow - Product Documentation

## Getting Started

### Creating an Account
1. Visit https://app.techflow.io/signup
2. Enter your email and create a password
3. Verify your email address
4. Set up your workspace name
5. Invite team members

### Password Reset
1. Go to https://app.techflow.io/forgot-password
2. Enter your registered email
3. Check your inbox for the reset link (valid for 24 hours)
4. Create a new password (minimum 8 characters, must include number and special character)

## Features

### Task Management
- **Creating Tasks**: Click "+" button or press "T" shortcut. Add title, description, assignee, due date, and priority.
- **Kanban Board**: Drag and drop tasks between columns (To Do, In Progress, Review, Done)
- **List View**: Toggle between Kanban and List view using the view switcher
- **Subtasks**: Break tasks into smaller items. Click "Add subtask" within any task
- **Labels**: Color-coded labels for categorization (Bug, Feature, Enhancement, etc.)
- **Filters**: Filter by assignee, priority, label, or date range

### Team Collaboration
- **Comments**: Add comments on any task. Use @mentions to notify team members
- **Real-time Chat**: Built-in messaging. Create channels or DM team members
- **File Sharing**: Attach files up to 100MB per file. Supports all common formats
- **Document Editor**: Collaborative document editing with version history

### Integrations
- **Slack**: Two-way sync. Get task notifications in Slack, create tasks from Slack
- **GitHub**: Link pull requests to tasks. Auto-update task status on merge
- **Jira**: Import existing Jira projects. Bi-directional sync available on Business plan
- **Google Calendar**: Sync due dates with Google Calendar
- **API**: RESTful API available on Pro plan and above. Documentation at api.techflow.io

### API Documentation
- **Authentication**: API key-based. Generate keys in Settings > API
- **Rate Limits**: Free: 100 req/hr, Pro: 1,000 req/hr, Business: 10,000 req/hr
- **Endpoints**:
  - `GET /api/v1/tasks` - List all tasks
  - `POST /api/v1/tasks` - Create a task
  - `PUT /api/v1/tasks/:id` - Update a task
  - `DELETE /api/v1/tasks/:id` - Delete a task
  - `GET /api/v1/projects` - List all projects
  - `POST /api/v1/projects` - Create a project

### Automation & Workflows
- **Triggers**: When task status changes, when due date approaches, when assigned
- **Actions**: Send notification, move to project, update priority, create subtask
- **Templates**: Pre-built workflow templates for common processes

### Time Tracking
- **Timer**: Built-in timer on each task. Click play/pause to track time
- **Manual Entry**: Add time entries manually with date and description
- **Reports**: Weekly/monthly time reports by project, team, or individual
- **Export**: Export time data as CSV or PDF

### Settings & Administration
- **Workspace Settings**: Name, logo, default timezone, notification preferences
- **User Roles**: Owner, Admin, Member, Guest
- **SSO/SAML**: Available on Business plan. Supports Okta, Azure AD, Google Workspace
- **Data Export**: Export all workspace data in JSON format (Settings > Data > Export)
- **Account Deletion**: Contact support or go to Settings > Account > Delete Account

## Troubleshooting

### Common Issues
1. **Can't log in**: Clear browser cache, try incognito mode, or reset password
2. **Notifications not working**: Check Settings > Notifications, ensure browser permissions
3. **Slow performance**: Clear browser cache, disable unused extensions, try different browser
4. **File upload fails**: Check file size (<100MB), check file format, check storage quota
5. **API returns 403**: Verify API key, check plan limits, ensure correct permissions
6. **Integration not syncing**: Disconnect and reconnect, check third-party service status
7. **Mobile app issues**: Update to latest version, clear app cache, reinstall if needed

### System Requirements
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS 15+ or Android 12+
- **Internet**: Minimum 5 Mbps recommended

### Data & Security
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Backups**: Daily automated backups, 30-day retention
- **Compliance**: SOC 2 Type II, GDPR compliant
- **Uptime SLA**: 99.9% for Business plan, 99.99% for Enterprise
