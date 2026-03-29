#!/usr/bin/env node
/**
 * MCP Email Server - Send emails via Gmail API
 * 
 * Usage:
 *   npx @modelcontextprotocol/server-email
 * 
 * Or run directly:
 *   node mcp-email-server.js
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { google } from 'googleapis';
import { authenticate } from '@google-cloud/local-auth';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuration
const GMAIL_CREDENTIALS_PATH = process.env.GMAIL_CREDENTIALS_PATH || 
  path.join(process.env.HOME || process.env.USERPROFILE, '.gmail', 'credentials.json');
const GMAIL_TOKEN_PATH = process.env.GMAIL_TOKEN_PATH || 
  path.join(process.env.HOME || process.env.USERPROFILE, '.gmail', 'token.json');

// SCOPES for Gmail API
const SCOPES = ['https://www.googleapis.com/auth/gmail.send'];

/**
 * Load or refresh OAuth credentials
 */
async function getGmailClient() {
  const credentialsPath = GMAIL_CREDENTIALS_PATH;
  const tokenPath = GMAIL_TOKEN_PATH;
  
  // Check if credentials exist
  if (!fs.existsSync(credentialsPath)) {
    throw new Error(
      `Gmail credentials not found at: ${credentialsPath}\n` +
      `Please download credentials.json from Google Cloud Console and save to this location.`
    );
  }
  
  const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf-8'));
  
  // Try to load existing token
  let oauth2Client;
  if (fs.existsSync(tokenPath)) {
    const token = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
    oauth2Client = new google.auth.OAuth2(
      credentials.client_id,
      credentials.client_secret,
      credentials.redirect_uris[0]
    );
    oauth2Client.setCredentials(token);
    
    // Check if token needs refresh
    if (oauth2Client.credentials.expiry_date) {
      const expiry = new Date(oauth2Client.credentials.expiry_date);
      if (expiry < new Date()) {
        console.error('Token expired, attempting refresh...');
        try {
          const { credentials: newCredentials } = await oauth2Client.refreshAccessToken();
          fs.writeFileSync(tokenPath, JSON.stringify(newCredentials));
          console.error('Token refreshed successfully');
        } catch (err) {
          throw new Error('Token refresh failed. Please re-authenticate.');
        }
      }
    }
  } else {
    throw new Error(
      `Gmail token not found at: ${tokenPath}\n` +
      `Please run OAuth setup to authenticate.`
    );
  }
  
  return google.gmail({ version: 'v1', auth: oauth2Client });
}

/**
 * Create email message
 */
function createEmail(to, subject, body, attachments = []) {
  const mimeParts = [];
  
  // Headers
  let str = `To: ${to}\r\n`;
  str += `Subject: ${subject}\r\n`;
  str += `MIME-Version: 1.0\r\n`;
  str += `Content-Type: multipart/mixed; boundary="BOUNDARY"\r\n\r\n`;
  
  // Body
  str += `--BOUNDARY\r\n`;
  str += `Content-Type: text/plain; charset="UTF-8"\r\n\r\n`;
  str += `${body}\r\n\r\n`;
  
  // Attachments
  for (const attachment of attachments) {
    const fileData = fs.readFileSync(attachment.path);
    const base64Data = fileData.toString('base64');
    
    str += `--BOUNDARY\r\n`;
    str += `Content-Type: ${attachment.mimeType || 'application/octet-stream'}\r\n`;
    str += `Content-Disposition: attachment; filename="${attachment.filename || path.basename(attachment.path)}"\r\n`;
    str += `Content-Transfer-Encoding: base64\r\n\r\n`;
    str += `${base64Data}\r\n\r\n`;
  }
  
  str += `--BOUNDARY--`;
  
  const encodedEmail = Buffer.from(str)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  
  return { raw: encodedEmail };
}

/**
 * Send email via Gmail API
 */
async function sendEmail({ to, subject, body, attachments = [] }) {
  const gmail = await getGmailClient();
  
  const email = createEmail(to, subject, body, attachments);
  
  const response = await gmail.users.messages.send({
    userId: 'me',
    requestBody: email,
  });
  
  return {
    success: true,
    messageId: response.data.id,
    threadId: response.data.threadId,
    labelIds: response.data.labelIds,
  };
}

/**
 * Create draft email
 */
async function createDraft({ to, subject, body, attachments = [] }) {
  const gmail = await getGmailClient();
  
  const email = createEmail(to, subject, body, attachments);
  
  const response = await gmail.users.drafts.create({
    userId: 'me',
    requestBody: {
      message: email,
    },
  });
  
  return {
    success: true,
    draftId: response.data.id,
    messageId: response.data.message.id,
  };
}

/**
 * Search emails
 */
async function searchEmails({ query, maxResults = 10 }) {
  const gmail = await getGmailClient();
  
  const response = await gmail.users.messages.list({
    userId: 'me',
    q: query,
    maxResults: Math.min(maxResults, 500),
  });
  
  const messages = response.data.messages || [];
  
  // Get full message details
  const emails = await Promise.all(
    messages.slice(0, maxResults).map(async (msg) => {
      const full = await gmail.users.messages.get({
        userId: 'me',
        id: msg.id,
        format: 'metadata',
        metadataHeaders: ['From', 'To', 'Subject', 'Date'],
      });
      
      const headers = {};
      full.data.payload.headers.forEach(h => {
        headers[h.name.toLowerCase()] = h.value;
      });
      
      return {
        id: msg.id,
        threadId: msg.threadId,
        from: headers.from,
        to: headers.to,
        subject: headers.subject,
        date: headers.date,
      };
    })
  );
  
  return {
    success: true,
    count: emails.length,
    emails,
  };
}

// Create MCP Server
const server = new Server(
  {
    name: 'email-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'email_send',
        description: 'Send an email via Gmail. Requires human approval for sensitive actions.',
        inputSchema: {
          type: 'object',
          properties: {
            to: {
              type: 'string',
              description: 'Recipient email address',
            },
            subject: {
              type: 'string',
              description: 'Email subject line',
            },
            body: {
              type: 'string',
              description: 'Email body text',
            },
            attachments: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  path: {
                    type: 'string',
                    description: 'Absolute path to attachment file',
                  },
                  filename: {
                    type: 'string',
                    description: 'Optional filename for attachment',
                  },
                  mimeType: {
                    type: 'string',
                    description: 'Optional MIME type (auto-detected if not provided)',
                  },
                },
                required: ['path'],
              },
              description: 'Optional file attachments',
            },
          },
          required: ['to', 'subject', 'body'],
        },
      },
      {
        name: 'email_draft',
        description: 'Create a draft email (doesn\'t send). Good for review before sending.',
        inputSchema: {
          type: 'object',
          properties: {
            to: {
              type: 'string',
              description: 'Recipient email address',
            },
            subject: {
              type: 'string',
              description: 'Email subject line',
            },
            body: {
              type: 'string',
              description: 'Email body text',
            },
            attachments: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  path: {
                    type: 'string',
                    description: 'Absolute path to attachment file',
                  },
                },
                required: ['path'],
              },
              description: 'Optional file attachments',
            },
          },
          required: ['to', 'subject', 'body'],
        },
      },
      {
        name: 'email_search',
        description: 'Search emails in Gmail',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Gmail search query (e.g., "from:client@example.com", "subject:invoice")',
            },
            maxResults: {
              type: 'number',
              description: 'Maximum number of results (default: 10, max: 500)',
              default: 10,
            },
          },
          required: ['query'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case 'email_send': {
        const result = await sendEmail(args);
        return {
          content: [
            {
              type: 'text',
              text: `✅ Email sent successfully!\n\nMessage ID: ${result.messageId}\nThread ID: ${result.threadId}`,
            },
          ],
        };
      }
      
      case 'email_draft': {
        const result = await createDraft(args);
        return {
          content: [
            {
              type: 'text',
              text: `✅ Draft created successfully!\n\nDraft ID: ${result.draftId}\nMessage ID: ${result.messageId}\n\nYou can review and send from Gmail drafts folder.`,
            },
          ],
        };
      }
      
      case 'email_search': {
        const result = await searchEmails(args);
        const emailList = result.emails
          .map((e) => `From: ${e.from}\nSubject: ${e.subject}\nDate: ${e.date}\n---`)
          .join('\n');
        
        return {
          content: [
            {
              type: 'text',
              text: `Found ${result.count} email(s):\n\n${emailList}`,
            },
          ],
        };
      }
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ Error: ${error.message}`,
          isError: true,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  console.error('MCP Email Server starting...');
  console.error(`Credentials: ${GMAIL_CREDENTIALS_PATH}`);
  console.error(`Token: ${GMAIL_TOKEN_PATH}`);
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('MCP Email Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
