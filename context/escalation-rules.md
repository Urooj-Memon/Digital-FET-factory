# Escalation Rules - Customer Success FTE

## Immediate Escalation (Priority: URGENT)
These scenarios MUST be escalated to human agents immediately:

1. **Pricing & Billing**
   - Customer asks about pricing changes
   - Customer requests a refund
   - Billing disputes or charge complaints
   - Enterprise pricing inquiries

2. **Legal & Compliance**
   - Customer mentions "lawyer", "legal", "sue", or "attorney"
   - GDPR data deletion requests
   - Data breach concerns
   - Contract/SLA disputes

3. **Angry/Frustrated Customers**
   - Sentiment score below 0.3
   - Customer uses profanity or aggressive language
   - Customer threatens to cancel
   - Customer explicitly demands human support

4. **Technical Emergencies**
   - Data loss reported
   - Security vulnerability reported
   - Service completely unavailable for customer
   - Account compromise suspected

## Conditional Escalation (Priority: HIGH)
Escalate if the AI cannot resolve within 2 interactions:

1. **Complex Technical Issues**
   - API integration failures
   - SSO/SAML configuration problems
   - Data migration assistance
   - Custom workflow debugging

2. **Account Management**
   - Plan upgrade/downgrade requests
   - Account ownership transfer
   - Team member permission issues
   - Workspace merging requests

## Self-Resolve (Priority: NORMAL)
The AI should handle these independently:

1. **General Questions** - Product features, how-to guidance
2. **Password Resets** - Guide through reset process
3. **Basic Troubleshooting** - Clear cache, check settings
4. **Feature Requests** - Log and acknowledge
5. **Feedback** - Accept and categorize

## Channel-Specific Rules

### Email
- Always respond within 5 minutes
- Include ticket reference number
- CC the customer's account manager for Enterprise customers

### WhatsApp
- Respond within 30 seconds
- If customer sends "human" or "agent", escalate immediately
- Keep responses under 300 characters

### Web Form
- Acknowledge submission immediately
- Send email notification with ticket ID
- Provide estimated response time

## Escalation Format
When escalating, always include:
- Customer ID and contact info
- Full conversation history
- Channel of origin
- Sentiment analysis summary
- Reason for escalation
- Priority level
