// Email Automation System - Frontend Application
class EmailAutomationApp {
    constructor() {
        this.config = {};
        this.isRunning = false;
        this.ws = null;
        this.init();
    }

    init() {
        this.initializeLucide();
        this.bindEvents();
        this.loadConfiguration();
        this.startWebSocket();
        this.updateStats();
    }

    initializeLucide() {
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    bindEvents() {
        // Settings modal
        document.getElementById('settings-btn').addEventListener('click', () => this.openSettings());
        document.getElementById('close-settings').addEventListener('click', () => this.closeSettings());
        
        // Logs modal
        document.getElementById('view-logs-btn').addEventListener('click', () => this.openLogs());
        document.getElementById('close-logs').addEventListener('click', () => this.closeLogs());
        
        // System controls
        document.getElementById('start-stop-btn').addEventListener('click', () => this.toggleSystem());
        
        // Quick actions
        document.getElementById('test-email-btn').addEventListener('click', () => this.testEmailConnection());
        document.getElementById('export-config-btn').addEventListener('click', () => this.exportConfiguration());
        
        // Close modals on outside click
        document.getElementById('settings-modal').addEventListener('click', (e) => {
            if (e.target.id === 'settings-modal') this.closeSettings();
        });
        document.getElementById('logs-modal').addEventListener('click', (e) => {
            if (e.target.id === 'logs-modal') this.closeLogs();
        });
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                this.config = await response.json();
                this.updateStatusIndicators();
            }
        } catch (error) {
            console.error('Failed to load configuration:', error);
        }
    }

    async saveConfiguration(config) {
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                this.config = config;
                this.updateStatusIndicators();
                this.showNotification('Configuration saved successfully!', 'success');
                return true;
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            console.error('Failed to save configuration:', error);
            this.showNotification('Failed to save configuration', 'error');
            return false;
        }
    }

    openSettings() {
        const modal = document.getElementById('settings-modal');
        const content = document.getElementById('settings-content');
        
        content.innerHTML = this.generateSettingsForm();
        modal.classList.remove('hidden');
        
        // Re-initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Bind form events
        this.bindSettingsEvents();
    }

    closeSettings() {
        document.getElementById('settings-modal').classList.add('hidden');
    }

    generateSettingsForm() {
        return `
            <div class="space-y-8">
                <!-- Navigation Tabs -->
                <div class="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                    <button class="settings-tab active px-4 py-2 rounded-md text-sm font-medium" data-tab="imap">
                        <i data-lucide="inbox" class="w-4 h-4 inline mr-2"></i>IMAP
                    </button>
                    <button class="settings-tab px-4 py-2 rounded-md text-sm font-medium" data-tab="smtp">
                        <i data-lucide="send" class="w-4 h-4 inline mr-2"></i>SMTP
                    </button>
                    <button class="settings-tab px-4 py-2 rounded-md text-sm font-medium" data-tab="openai">
                        <i data-lucide="brain" class="w-4 h-4 inline mr-2"></i>OpenAI
                    </button>
                    <button class="settings-tab px-4 py-2 rounded-md text-sm font-medium" data-tab="google-chat">
                        <i data-lucide="message-circle" class="w-4 h-4 inline mr-2"></i>Google Chat
                    </button>
                    <button class="settings-tab px-4 py-2 rounded-md text-sm font-medium" data-tab="system">
                        <i data-lucide="settings" class="w-4 h-4 inline mr-2"></i>System
                    </button>
                </div>

                <!-- IMAP Settings -->
                <div id="imap-settings" class="settings-panel">
                    <h3 class="text-lg font-semibold mb-4">IMAP Email Settings (Incoming)</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">IMAP Host</label>
                            <input type="text" id="imap-host" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.imap_host || 'imap.gmail.com'}" placeholder="imap.gmail.com">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">IMAP Port</label>
                            <input type="number" id="imap-port" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.imap_port || 993}" placeholder="993">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                            <input type="email" id="imap-email" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.imap_email || ''}" placeholder="your-email@domain.com">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Password/App Password</label>
                            <input type="password" id="imap-password" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.imap_password || ''}" placeholder="Your password or app password">
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Check Interval (seconds)</label>
                            <input type="number" id="imap-interval" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.imap_check_interval || 30}" placeholder="30">
                        </div>
                    </div>
                </div>

                <!-- SMTP Settings -->
                <div id="smtp-settings" class="settings-panel hidden">
                    <h3 class="text-lg font-semibold mb-4">SMTP Email Settings (Outgoing)</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">SMTP Host</label>
                            <input type="text" id="smtp-host" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.smtp_host || 'smtp.gmail.com'}" placeholder="smtp.gmail.com">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">SMTP Port</label>
                            <input type="number" id="smtp-port" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.smtp_port || 587}" placeholder="587">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                            <input type="email" id="smtp-email" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.smtp_email || ''}" placeholder="your-email@domain.com">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Password/App Password</label>
                            <input type="password" id="smtp-password" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.smtp_password || ''}" placeholder="Your password or app password">
                        </div>
                    </div>
                </div>

                <!-- OpenAI Settings -->
                <div id="openai-settings" class="settings-panel hidden">
                    <h3 class="text-lg font-semibold mb-4">OpenAI Configuration</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                            <input type="password" id="openai-api-key" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.openai_api_key || ''}" placeholder="sk-...">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Model</label>
                            <select id="openai-model" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="gpt-4o" ${this.config.openai_model === 'gpt-4o' ? 'selected' : ''}>GPT-4o</option>
                                <option value="gpt-4o-mini" ${this.config.openai_model === 'gpt-4o-mini' ? 'selected' : ''}>GPT-4o Mini</option>
                                <option value="gpt-4-turbo" ${this.config.openai_model === 'gpt-4-turbo' ? 'selected' : ''}>GPT-4 Turbo</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Urgent Timeout (minutes)</label>
                            <input type="number" id="urgent-timeout" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.urgent_timeout_minutes || 10}" placeholder="10">
                        </div>
                    </div>
                </div>

                <!-- Google Chat Settings -->
                <div id="google-chat-settings" class="settings-panel hidden">
                    <h3 class="text-lg font-semibold mb-4">Google Chat Integration</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Webhook URL</label>
                            <input type="url" id="chat-webhook-url" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.google_chat_webhook_url || ''}" placeholder="https://chat.googleapis.com/v1/spaces/.../messages">
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">OAuth Client ID (Optional)</label>
                                <input type="text" id="chat-client-id" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                       value="${this.config.google_chat_oauth_client_id || ''}" placeholder="Your OAuth client ID">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">OAuth Client Secret (Optional)</label>
                                <input type="password" id="chat-client-secret" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                       value="${this.config.google_chat_oauth_client_secret || ''}" placeholder="Your OAuth client secret">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- System Settings -->
                <div id="system-settings" class="settings-panel hidden">
                    <h3 class="text-lg font-semibold mb-4">System Configuration</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Log Level</label>
                            <select id="log-level" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="DEBUG" ${this.config.log_level === 'DEBUG' ? 'selected' : ''}>DEBUG</option>
                                <option value="INFO" ${this.config.log_level === 'INFO' ? 'selected' : ''}>INFO</option>
                                <option value="WARNING" ${this.config.log_level === 'WARNING' ? 'selected' : ''}>WARNING</option>
                                <option value="ERROR" ${this.config.log_level === 'ERROR' ? 'selected' : ''}>ERROR</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Log File</label>
                            <input type="text" id="log-file" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.log_file || 'email_automation.log'}" placeholder="email_automation.log">
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Redis URL (Optional)</label>
                            <input type="text" id="redis-url" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                   value="${this.config.redis_url || ''}" placeholder="redis://localhost:6379/0">
                        </div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                    <button id="test-connections" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors">
                        <i data-lucide="wifi" class="w-4 h-4 inline mr-2"></i>Test Connections
                    </button>
                    <button id="save-config" class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                        <i data-lucide="save" class="w-4 h-4 inline mr-2"></i>Save Configuration
                    </button>
                </div>
            </div>
        `;
    }

    bindSettingsEvents() {
        // Tab switching
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchSettingsTab(tabName);
            });
        });

        // Save configuration
        document.getElementById('save-config').addEventListener('click', () => {
            this.saveSettingsForm();
        });

        // Test connections
        document.getElementById('test-connections').addEventListener('click', () => {
            this.testAllConnections();
        });
    }

    switchSettingsTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.remove('active', 'bg-white', 'text-gray-900', 'shadow-sm');
            tab.classList.add('text-gray-500');
        });
        
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        activeTab.classList.add('active', 'bg-white', 'text-gray-900', 'shadow-sm');
        activeTab.classList.remove('text-gray-500');

        // Update panels
        document.querySelectorAll('.settings-panel').forEach(panel => {
            panel.classList.add('hidden');
        });
        document.getElementById(`${tabName}-settings`).classList.remove('hidden');
    }

    async saveSettingsForm() {
        const config = {
            // IMAP settings
            imap_host: document.getElementById('imap-host').value,
            imap_port: parseInt(document.getElementById('imap-port').value),
            imap_email: document.getElementById('imap-email').value,
            imap_password: document.getElementById('imap-password').value,
            imap_check_interval: parseInt(document.getElementById('imap-interval').value),
            
            // SMTP settings
            smtp_host: document.getElementById('smtp-host').value,
            smtp_port: parseInt(document.getElementById('smtp-port').value),
            smtp_email: document.getElementById('smtp-email').value,
            smtp_password: document.getElementById('smtp-password').value,
            
            // OpenAI settings
            openai_api_key: document.getElementById('openai-api-key').value,
            openai_model: document.getElementById('openai-model').value,
            urgent_timeout_minutes: parseInt(document.getElementById('urgent-timeout').value),
            
            // Google Chat settings
            google_chat_webhook_url: document.getElementById('chat-webhook-url').value,
            google_chat_oauth_client_id: document.getElementById('chat-client-id').value,
            google_chat_oauth_client_secret: document.getElementById('chat-client-secret').value,
            
            // System settings
            log_level: document.getElementById('log-level').value,
            log_file: document.getElementById('log-file').value,
            redis_url: document.getElementById('redis-url').value
        };

        const success = await this.saveConfiguration(config);
        if (success) {
            this.closeSettings();
        }
    }

    async testAllConnections() {
        const button = document.getElementById('test-connections');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 inline mr-2 animate-spin"></i>Testing...';
        button.disabled = true;

        try {
            const response = await fetch('/api/test-connections', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.getCurrentFormConfig())
            });

            const results = await response.json();
            this.showConnectionTestResults(results);
        } catch (error) {
            this.showNotification('Failed to test connections', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    }

    getCurrentFormConfig() {
        return {
            imap_host: document.getElementById('imap-host').value,
            imap_port: parseInt(document.getElementById('imap-port').value),
            imap_email: document.getElementById('imap-email').value,
            imap_password: document.getElementById('imap-password').value,
            smtp_host: document.getElementById('smtp-host').value,
            smtp_port: parseInt(document.getElementById('smtp-port').value),
            smtp_email: document.getElementById('smtp-email').value,
            smtp_password: document.getElementById('smtp-password').value,
            openai_api_key: document.getElementById('openai-api-key').value,
            google_chat_webhook_url: document.getElementById('chat-webhook-url').value
        };
    }

    showConnectionTestResults(results) {
        const messages = [];
        
        if (results.imap) {
            messages.push(`IMAP: ${results.imap.success ? '✅ Connected' : '❌ Failed - ' + results.imap.error}`);
        }
        if (results.smtp) {
            messages.push(`SMTP: ${results.smtp.success ? '✅ Connected' : '❌ Failed - ' + results.smtp.error}`);
        }
        if (results.openai) {
            messages.push(`OpenAI: ${results.openai.success ? '✅ Connected' : '❌ Failed - ' + results.openai.error}`);
        }
        if (results.google_chat) {
            messages.push(`Google Chat: ${results.google_chat.success ? '✅ Connected' : '❌ Failed - ' + results.google_chat.error}`);
        }

        this.showNotification(messages.join('<br>'), results.all_success ? 'success' : 'error');
    }

    async toggleSystem() {
        const button = document.getElementById('start-stop-btn');
        const isCurrentlyRunning = this.isRunning;

        if (isCurrentlyRunning) {
            // Stop system
            try {
                await fetch('/api/system/stop', { method: 'POST' });
                this.isRunning = false;
                button.textContent = 'Start System';
                button.className = 'px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors';
                this.updateStatusIndicators();
                this.showNotification('System stopped', 'info');
            } catch (error) {
                this.showNotification('Failed to stop system', 'error');
            }
        } else {
            // Start system
            try {
                const response = await fetch('/api/system/start', { method: 'POST' });
                if (response.ok) {
                    this.isRunning = true;
                    button.textContent = 'Stop System';
                    button.className = 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors';
                    this.updateStatusIndicators();
                    this.showNotification('System started', 'success');
                } else {
                    throw new Error('Failed to start system');
                }
            } catch (error) {
                this.showNotification('Failed to start system', 'error');
            }
        }
    }

    async testEmailConnection() {
        try {
            const response = await fetch('/api/test-email', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Email connection test successful!', 'success');
            } else {
                this.showNotification(`Email test failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to test email connection', 'error');
        }
    }

    async exportConfiguration() {
        try {
            const response = await fetch('/api/config/export');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'email-automation-config.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showNotification('Configuration exported successfully!', 'success');
        } catch (error) {
            this.showNotification('Failed to export configuration', 'error');
        }
    }

    openLogs() {
        const modal = document.getElementById('logs-modal');
        const content = document.getElementById('logs-content');
        
        modal.classList.remove('hidden');
        this.loadLogs();
    }

    closeLogs() {
        document.getElementById('logs-modal').classList.add('hidden');
    }

    async loadLogs() {
        try {
            const response = await fetch('/api/logs');
            const logs = await response.text();
            document.getElementById('logs-content').textContent = logs;
        } catch (error) {
            document.getElementById('logs-content').textContent = 'Failed to load logs';
        }
    }

    startWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            // Reconnect after 5 seconds
            setTimeout(() => this.startWebSocket(), 5000);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status_update':
                this.updateStatusIndicators(data.status);
                break;
            case 'stats_update':
                this.updateStats(data.stats);
                break;
            case 'activity':
                this.addActivityItem(data.activity);
                break;
            case 'log':
                this.addLogEntry(data.log);
                break;
        }
    }

    updateStatusIndicators(status = null) {
        if (!status) {
            // Default offline state
            document.querySelectorAll('[id$="-status"]').forEach(el => {
                el.className = 'w-3 h-3 bg-gray-400 rounded-full';
            });
            document.querySelectorAll('[id$="-status-text"]').forEach(el => {
                el.textContent = 'Not Connected';
            });
            return;
        }

        // Update individual status indicators
        this.updateStatusIndicator('imap', status.imap);
        this.updateStatusIndicator('openai', status.openai);
        this.updateStatusIndicator('smtp', status.smtp);
        this.updateStatusIndicator('chat', status.google_chat);
    }

    updateStatusIndicator(service, isConnected) {
        const indicator = document.getElementById(`${service}-status`);
        const text = document.getElementById(`${service}-status-text`);
        
        if (isConnected) {
            indicator.className = 'w-3 h-3 bg-green-500 rounded-full';
            text.textContent = 'Connected';
        } else {
            indicator.className = 'w-3 h-3 bg-red-500 rounded-full';
            text.textContent = 'Disconnected';
        }
    }

    updateStats(stats = null) {
        if (!stats) {
            // Default values
            document.getElementById('emails-processed').textContent = '0';
            document.getElementById('ai-responses').textContent = '0';
            document.getElementById('human-escalations').textContent = '0';
            document.getElementById('success-rate').textContent = '0%';
            return;
        }

        document.getElementById('emails-processed').textContent = stats.emails_processed || 0;
        document.getElementById('ai-responses').textContent = stats.ai_responses || 0;
        document.getElementById('human-escalations').textContent = stats.human_escalations || 0;
        document.getElementById('success-rate').textContent = `${stats.success_rate || 0}%`;
    }

    addActivityItem(activity) {
        const feed = document.getElementById('activity-feed');
        
        // Remove "no activity" message if present
        const noActivity = feed.querySelector('.text-center');
        if (noActivity) {
            noActivity.remove();
        }
        
        const item = document.createElement('div');
        item.className = 'flex items-start space-x-3 p-3 bg-gray-50 rounded-lg';
        item.innerHTML = `
            <div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
            <div class="flex-1">
                <p class="text-sm text-gray-900">${activity.message}</p>
                <p class="text-xs text-gray-500">${new Date(activity.timestamp).toLocaleTimeString()}</p>
            </div>
        `;
        
        feed.insertBefore(item, feed.firstChild);
        
        // Keep only last 10 items
        while (feed.children.length > 10) {
            feed.removeChild(feed.lastChild);
        }
    }

    addLogEntry(log) {
        const logsContent = document.getElementById('logs-content');
        if (logsContent && !logsContent.closest('#logs-modal').classList.contains('hidden')) {
            logsContent.textContent += log + '\n';
            logsContent.scrollTop = logsContent.scrollHeight;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-md ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div>${message}</div>
                <button class="ml-4 text-white hover:text-gray-200">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('button').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EmailAutomationApp();
});
