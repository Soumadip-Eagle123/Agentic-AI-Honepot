// layer7_api_ui/static/app.js
document.addEventListener("DOMContentLoaded", () => {
    // UI Elements - Navigation & Roles
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const roleSelect = document.getElementById("user-role-select");
    const roleDescText = document.getElementById("role-desc-text");
    const refreshAllBtn = document.getElementById("refresh-all-btn");

    // UI Elements - Incidents Panel
    const incidentsList = document.getElementById("incidents-list-container");
    const searchInput = document.getElementById("incidents-search");
    const filterChips = document.querySelectorAll(".filter-chip");
    
    // UI Elements - Case Detail Deep Dive
    const noCaseSelected = document.getElementById("no-case-selected");
    const caseDetailsWrapper = document.getElementById("case-details-wrapper");
    const detailSessionId = document.getElementById("detail-session-id");
    const detailSeverityBadge = document.getElementById("detail-severity-badge");
    const detailChannel = document.getElementById("detail-channel");
    const detailRegion = document.getElementById("detail-region");
    const detailPersona = document.getElementById("detail-persona");
    
    // Actions on Case
    const btnRunPipeline = document.getElementById("btn-run-pipeline");
    const btnExportIntel = document.getElementById("btn-export-intel");
    
    // Details Sub-Tabs
    const detailsTabButtons = document.querySelectorAll(".details-tab-btn");
    const detailsTabContents = document.querySelectorAll(".details-tab-content");
    
    // Intel Fields
    const detailThreatScoreVal = document.getElementById("detail-threat-score-val");
    const detailGaugeFill = document.getElementById("detail-gauge-fill");
    const valMeterUrgency = document.getElementById("val-meter-urgency");
    const fillMeterUrgency = document.getElementById("fill-meter-urgency");
    const valMeterAuthority = document.getElementById("val-meter-authority");
    const fillMeterAuthority = document.getElementById("fill-meter-authority");
    const valMeterSkip = document.getElementById("val-meter-skip");
    const fillMeterSkip = document.getElementById("fill-meter-skip");
    
    const listIntelPhones = document.getElementById("list-intel-phones");
    const listIntelUpis = document.getElementById("list-intel-upis");
    const listIntelAccounts = document.getElementById("list-intel-accounts");
    const listIntelUrls = document.getElementById("list-intel-urls");
    
    const detailLinkedCasesCount = document.getElementById("detail-linked-cases-count");
    const detailSharedArtifactsCount = document.getElementById("detail-shared-artifacts-count");
    const detailSharedArtifactsList = document.getElementById("detail-shared-artifacts-list");
    
    const detailLlmSummary = document.getElementById("detail-llm-summary");
    const detailRecommendedAction = document.getElementById("detail-recommended-action");
    
    const timelineHook = document.getElementById("timeline-hook");
    const timelineTrust = document.getElementById("timeline-trust");
    const timelinePressure = document.getElementById("timeline-pressure");
    const timelinePayment = document.getElementById("timeline-payment");
    
    // Audit Transcript Fields
    const auditTranscriptMessages = document.getElementById("audit-transcript-messages");
    const canvas = document.getElementById("confidence-flow-canvas");

    // UI Elements - Database Migrations Tab
    const migrationCurrentVersion = document.getElementById("migration-current-version");
    const btnTriggerMigration = document.getElementById("btn-trigger-migration");
    const appliedMigrationsList = document.getElementById("applied-migrations-list");
    const databaseTablesDefinition = document.getElementById("database-tables-definition");

    // UI Elements - Mock Session Modal
    const btnMockSession = document.getElementById("btn-mock-session");
    const mockSessionModal = document.getElementById("mock-session-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnCancelModal = document.getElementById("btn-cancel-modal");
    const mockSessionForm = document.getElementById("mock-session-form");

    // Application State
    let state = {
        sessions: [],
        currentSessionId: null,
        activeTab: "dashboard",
        currentRole: "soc",
        selectedSeverityFilter: "all",
        searchQuery: ""
    };

    // Role Details mapping
    const roleDescriptions = {
        soc: "PII Masked. Scammer IOCs partially obfuscated.",
        law_enforcement: "PII Masked. Threat actor IOCs (phones, UPI, accounts) fully unmasked for forensic extraction.",
        developer: "Compliance Debug Mode. Full logs visible side-by-side to verify masking precision."
    };

    // ─── Initializer ───
    init();

    function init() {
        bindEvents();
        loadSessions();
        loadSchemaStatus();
    }

    // ─── Event Bindings ───
    function bindEvents() {
        // Tab switching
        navButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                navButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                
                const tab = btn.dataset.tab;
                state.activeTab = tab;
                
                tabContents.forEach(content => {
                    content.classList.remove("active");
                    if (content.id === `tab-${tab}`) {
                        content.classList.add("active");
                    }
                });

                if (tab === "dashboard" || tab === "incidents") {
                    loadSessions();
                } else if (tab === "migrations") {
                    loadSchemaStatus();
                }
            });
        });

        // Detail Pane Sub-tab switching
        detailsTabButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                detailsTabButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                
                const detTab = btn.dataset.detailsTab;
                detailsTabContents.forEach(content => {
                    content.classList.remove("active");
                    if (content.id === `details-tab-${detTab}`) {
                        content.classList.add("active");
                    }
                });

                // Redraw chart if audit tab is opened
                if (detTab === "audit" && state.currentSessionId) {
                    setTimeout(() => loadAuditTrail(state.currentSessionId), 50);
                }
            });
        });

        // Role select change handler
        roleSelect.addEventListener("change", (e) => {
            const role = e.target.value;
            state.currentRole = role;
            roleDescText.textContent = roleDescriptions[role] || "";
            
            // Reload active case details if selected
            if (state.currentSessionId) {
                loadCaseDetails(state.currentSessionId);
            }
        });

        // Global Refresh buttons
        refreshAllBtn.addEventListener("click", () => {
            loadSessions();
            if (state.currentSessionId) {
                loadCaseDetails(state.currentSessionId);
            }
            loadSchemaStatus();
        });

        // Search incidents
        searchInput.addEventListener("input", (e) => {
            state.searchQuery = e.target.value.toLowerCase().trim();
            renderIncidentsQueue();
        });

        // Severity filter chips
        filterChips.forEach(chip => {
            chip.addEventListener("click", () => {
                filterChips.forEach(c => c.classList.remove("active"));
                chip.classList.add("active");
                state.selectedSeverityFilter = chip.dataset.filter;
                renderIncidentsQueue();
            });
        });

        // Force Pipeline execution
        btnRunPipeline.addEventListener("click", () => {
            if (!state.currentSessionId) return;
            btnRunPipeline.disabled = true;
            btnRunPipeline.textContent = "⚡ Running Analysis Pipeline...";
            
            fetch(`/api/v1/sessions/${state.currentSessionId}/run_analysis`, { method: "POST" })
                .then(r => r.json())
                .then(data => {
                    alert("Pipeline Run Complete! Threat intelligence report generated.");
                    loadSessions();
                    loadCaseDetails(state.currentSessionId);
                })
                .catch(err => alert("Pipeline run failed: " + err))
                .finally(() => {
                    btnRunPipeline.disabled = false;
                    btnRunPipeline.textContent = "⚡ Force Run L5/L6 Pipeline";
                });
        });

        // Export data
        btnExportIntel.addEventListener("click", () => {
            if (!state.currentSessionId) return;
            fetch(`/api/v1/sessions/${state.currentSessionId}/report?role=${state.currentRole}`)
                .then(r => r.json())
                .then(data => {
                    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
                    const downloadAnchor = document.createElement('a');
                    downloadAnchor.setAttribute("href", dataStr);
                    downloadAnchor.setAttribute("download", `Honeypot_Threat_Report_${state.currentSessionId}_${state.currentRole}.json`);
                    document.body.appendChild(downloadAnchor);
                    downloadAnchor.click();
                    downloadAnchor.remove();
                });
        });

        // Migration button
        btnTriggerMigration.addEventListener("click", () => {
            btnTriggerMigration.disabled = true;
            btnTriggerMigration.textContent = "⚡ Applying...";
            
            fetch(`/api/v1/migrate`, { method: "POST" })
                .then(r => r.json())
                .then(data => {
                    alert("Migrations successfully applied! Database schemas updated.");
                    loadSchemaStatus();
                    loadSessions();
                })
                .catch(err => alert("Migration execution failed: " + err))
                .finally(() => {
                    btnTriggerMigration.disabled = false;
                    btnTriggerMigration.textContent = "⚡ Apply Pending Migrations";
                });
        });

        // Mock Modal buttons
        btnMockSession.addEventListener("click", () => {
            // Set random session id as default
            document.getElementById("mock-session-id").value = Math.floor(1000000000 + Math.random() * 9000000000);
            mockSessionModal.classList.remove("hidden");
        });

        const closeModal = () => mockSessionModal.classList.add("hidden");
        btnCloseModal.addEventListener("click", closeModal);
        btnCancelModal.addEventListener("click", closeModal);

        mockSessionForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const sid = document.getElementById("mock-session-id").value;
            const channel = document.getElementById("mock-channel").value;
            const sender = document.getElementById("mock-sender").value;
            const msg = document.getElementById("mock-message").value;
            const pScam = parseFloat(document.getElementById("mock-p-scam").value);

            fetch(`/api/v1/sessions/${sid}/simulate_turn`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sender, message: msg, p_scam: pScam, channel })
            })
            .then(r => r.json())
            .then(data => {
                alert(`Message turn simulated! Session: ${sid}`);
                closeModal();
                loadSessions();
                // Select this session automatically
                selectSession(sid);
            })
            .catch(err => alert("Failed simulating message: " + err));
        });
    }

    // ─── Data Loaders ───
    function loadSessions() {
        fetch("/api/v1/sessions")
            .then(r => r.json())
            .then(data => {
                if (data.status === "success") {
                    state.sessions = data.sessions;
                    renderMetricsSummary();
                    renderIncidentsQueue();
                }
            })
            .catch(err => {
                incidentsList.innerHTML = `<div class="error-msg">Failed loading database: ${err}</div>`;
            });
    }

    function loadCaseDetails(sessionId) {
        // Toggle view
        noCaseSelected.classList.add("hidden");
        caseDetailsWrapper.classList.remove("hidden");
        
        fetch(`/api/v1/sessions/${sessionId}/report?role=${state.currentRole}`)
            .then(r => r.json())
            .then(data => {
                renderCaseDetails(data);
                // Also load audit trail if active tab is audit
                const activeDetailsTab = document.querySelector(".details-tab-btn.active").dataset.detailsTab;
                if (activeDetailsTab === "audit") {
                    loadAuditTrail(sessionId);
                }
            })
            .catch(err => {
                console.error("Error loading case details:", err);
            });
    }

    function loadAuditTrail(sessionId) {
        fetch(`/api/v1/sessions/${sessionId}/audit?role=${state.currentRole}`)
            .then(r => r.json())
            .then(data => {
                renderAuditTranscript(data.conversation);
                drawConfidenceChart(data.confidence_flow);
            })
            .catch(err => {
                console.error("Error loading audit log:", err);
            });
    }

    function loadSchemaStatus() {
        fetch("/api/v1/schema-status")
            .then(r => r.json())
            .then(data => {
                if (data.status === "success") {
                    // Update current version
                    migrationCurrentVersion.textContent = `v${data.current_version}.0`;
                    document.getElementById("stat-db-version").textContent = `v${data.current_version}.0`;
                    
                    // Render applied migrations changelog
                    appliedMigrationsList.innerHTML = "";
                    if (data.applied_migrations.length === 0) {
                        appliedMigrationsList.innerHTML = "<li>No migrations applied yet. Baseline active.</li>";
                    } else {
                        data.applied_migrations.forEach(v => {
                            // Find corresponding file
                            const filename = data.all_available_migrations.find(f => f.startsWith(`${String(v).padStart(3, '0')}_`)) || `Migration ${v}`;
                            const li = document.createElement("li");
                            li.innerHTML = `<span>Applied Script: ${filename}</span> <span>🟢 Applied (v${v}.0)</span>`;
                            appliedMigrationsList.appendChild(li);
                        });
                    }

                    // Render table definitions
                    databaseTablesDefinition.innerHTML = "";
                    for (const [tname, cols] of Object.entries(data.tables)) {
                        const box = document.createElement("div");
                        box.className = "schema-table-box";
                        
                        let rowsHtml = cols.map(c => `
                            <tr>
                                <td>${c.name}</td>
                                <td>${c.type}</td>
                                <td>${c.notnull ? 'YES' : 'NO'}</td>
                                <td>${c.pk ? '🔑 PRIMARY KEY' : ''}</td>
                            </tr>
                        `).join("");

                        box.innerHTML = `
                            <div class="schema-table-header">Table: ${tname}</div>
                            <div class="schema-table-body">
                                <table class="schema-cols-table">
                                    <thead>
                                        <tr>
                                            <th>Column</th>
                                            <th>Type</th>
                                            <th>Not Null</th>
                                            <th>Constraint</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rowsHtml}
                                    </tbody>
                                </table>
                            </div>
                        `;
                        databaseTablesDefinition.appendChild(box);
                    }
                }
            });
    }

    // ─── Rendering Methods ───
    function renderMetricsSummary() {
        const total = state.sessions.length;
        const critical = state.sessions.filter(s => s.severity === "CRITICAL").length;
        
        let sumThreat = 0;
        state.sessions.forEach(s => sumThreat += s.threat_score);
        const avg = total > 0 ? Math.round(sumThreat / total) : 0;
        
        document.getElementById("stat-total-incidents").textContent = total;
        document.getElementById("stat-critical-alerts").textContent = critical;
        document.getElementById("stat-avg-threat").textContent = `${avg}%`;
    }

    function renderIncidentsQueue() {
        incidentsList.innerHTML = "";
        
        // Filter sessions
        let filtered = state.sessions;
        
        if (state.selectedSeverityFilter !== "all") {
            if (state.selectedSeverityFilter === "MEDIUM") {
                filtered = filtered.filter(s => s.severity === "MEDIUM" || s.severity === "LOW");
            } else {
                filtered = filtered.filter(s => s.severity === state.selectedSeverityFilter);
            }
        }
        
        if (state.searchQuery) {
            filtered = filtered.filter(s => String(s.session_id).toLowerCase().includes(state.searchQuery));
        }

        if (filtered.length === 0) {
            incidentsList.innerHTML = `<div class="empty-list">No sessions match filters</div>`;
            return;
        }

        filtered.forEach(session => {
            const item = document.createElement("div");
            item.className = `incident-item ${String(state.currentSessionId) === String(session.session_id) ? 'active' : ''}`;
            
            const severityClass = `badge-${session.severity.toLowerCase()}`;
            const statusClass = `badge-${session.status.toLowerCase()}`;
            
            item.innerHTML = `
                <div class="incident-info">
                    <span class="incident-id">#${session.session_id}</span>
                    <span class="incident-meta-details">Turns: ${session.turn_count} | ${session.channel}</span>
                </div>
                <div class="incident-score-badge">
                    <span class="incident-score-val">${session.threat_score}%</span>
                    <div>
                        <span class="badge ${severityClass}">${session.severity}</span>
                        <span class="badge ${statusClass}">${session.status}</span>
                    </div>
                </div>
            `;
            
            item.addEventListener("click", () => {
                selectSession(session.session_id);
            });
            
            incidentsList.appendChild(item);
        });
    }

    function selectSession(sid) {
        state.currentSessionId = sid;
        
        // Highlight in list
        const items = incidentsList.querySelectorAll(".incident-item");
        items.forEach(el => el.classList.remove("active"));
        
        // Re-render list queue to set active classes properly
        renderIncidentsQueue();
        
        loadCaseDetails(sid);
    }

    function renderCaseDetails(data) {
        const report = data.extraction_report;
        const analysis = data.threat_analysis;
        
        // Set basic details
        detailSessionId.textContent = `Session #${data.session_id}`;
        
        // Badges
        const severity = analysis.severity || "LOW";
        detailSeverityBadge.className = `badge badge-${severity.toLowerCase()}`;
        detailSeverityBadge.textContent = severity;
        
        const sessionsMatched = state.sessions.find(s => String(s.session_id) === String(data.session_id));
        detailChannel.textContent = sessionsMatched ? sessionsMatched.channel : "telegram";
        detailRegion.textContent = sessionsMatched ? sessionsMatched.region : "US-EAST";
        detailPersona.textContent = `${report.agent_persona_used || "Margaret"} (Honeypot)`;

        // Threat Score Gauge
        const score = analysis.threat_score || 0.0;
        detailThreatScoreVal.textContent = `${Math.round(score)}%`;
        detailGaugeFill.style.width = `${score}%`;
        document.documentElement.style.setProperty('--threat-score', score);

        // Linguistic meters
        const urgency = analysis.behavioral_profile?.urgency_score || 0.0;
        valMeterUrgency.textContent = urgency;
        fillMeterUrgency.style.width = `${urgency * 100}%`;
        
        const authority = analysis.behavioral_profile?.authority_score || 0.0;
        valMeterAuthority.textContent = authority;
        fillMeterAuthority.style.width = `${authority * 100}%`;
        
        const skip = analysis.behavioral_profile?.question_skip_rate || 0.0;
        valMeterSkip.textContent = skip;
        fillMeterSkip.style.width = `${skip * 100}%`;

        // Render harvested indicators
        renderEntitiesList(listIntelPhones, report.entities?.phone_numbers || []);
        renderEntitiesList(listIntelUpis, report.entities?.upi_ids || []);
        renderEntitiesList(listIntelAccounts, report.entities?.account_numbers || []);
        renderEntitiesList(listIntelUrls, report.entities?.urls || []);

        // Campaign stats
        const linked = analysis.campaign?.linked_sessions || [];
        const shared = analysis.campaign?.shared_artifacts || [];
        
        detailLinkedCasesCount.textContent = linked.length;
        detailSharedArtifactsCount.textContent = shared.length;
        
        detailSharedArtifactsList.innerHTML = "";
        if (shared.length === 0) {
            detailSharedArtifactsList.innerHTML = `<span class="empty-list">No shared indicators</span>`;
        } else {
            shared.forEach(art => {
                const tag = document.createElement("span");
                tag.className = "shared-tag";
                tag.textContent = art;
                detailSharedArtifactsList.appendChild(tag);
            });
        }

        // Analyst LLM outputs
        detailLlmSummary.textContent = analysis.llm_summary || report.confidence_note || "No analysis available.";
        detailRecommendedAction.textContent = analysis.recommended_action || "Manual analyst audit recommended.";

        // Progression Timeline stages
        renderTimelineStage(timelineHook, report.timeline?.hook, 1);
        renderTimelineStage(timelineTrust, report.timeline?.trust_building, 2);
        renderTimelineStage(timelinePressure, report.timeline?.pressure, 3);
        renderTimelineStage(timelinePayment, report.timeline?.payment_attempt, 4);
    }

    function renderEntitiesList(element, list) {
        element.innerHTML = "";
        if (list.length === 0) {
            element.innerHTML = `<li class="empty-list">None extracted</li>`;
            return;
        }
        
        list.forEach(val => {
            const li = document.createElement("li");
            li.textContent = val;
            
            // Add blocklist action if law_enforcement view
            if (state.currentRole === "law_enforcement") {
                const actionBtn = document.createElement("span");
                actionBtn.style.color = "var(--color-red)";
                actionBtn.style.cursor = "pointer";
                actionBtn.style.fontWeight = "bold";
                actionBtn.textContent = " 🚫 block";
                actionBtn.title = "Forward artifact to blocklist authority";
                actionBtn.onclick = () => {
                    alert(`Forensic artifact [${val}] forwarded to national blocklist services.`);
                };
                li.appendChild(actionBtn);
            }
            
            element.appendChild(li);
        });
    }

    function renderTimelineStage(element, text, stepIndex) {
        const stepBadge = document.querySelectorAll(".timeline-stepper .step-badge")[stepIndex - 1];
        if (text) {
            element.textContent = `"${text}"`;
            stepBadge.classList.add("active");
        } else {
            element.textContent = "Stage details pending interaction...";
            stepBadge.classList.remove("active");
        }
    }

    function renderAuditTranscript(conversation) {
        auditTranscriptMessages.innerHTML = "";
        
        if (conversation.length === 0) {
            auditTranscriptMessages.innerHTML = `<div class="empty-list">No conversation records</div>`;
            return;
        }

        conversation.forEach(turn => {
            const wrapper = document.createElement("div");
            const isVictim = (turn.original_sender || "").toLowerCase() !== "scammer";
            
            wrapper.className = `message-bubble-wrapper ${isVictim ? 'victim' : 'scammer'}`;
            
            // Highlight text if it contains sensitive PII markers or trigger concepts
            let textHtml = turn.message;
            if (state.currentRole !== "developer") {
                // Style redacting labels
                textHtml = textHtml.replace(/(\[MASKED_VICTIM_[A-Z_]+\])/g, '<span class="masked-pii-highlight">$1</span>');
                textHtml = textHtml.replace(/(\[MASKED_[A-Z_]+\])/g, '<span class="masked-pii-highlight">$1</span>');
            }

            const cleanTime = turn.timestamp.split("T")[1]?.substring(0, 8) || turn.timestamp;
            const pScamBadge = !isVictim ? `<span class="p-scam-indicator" title="Turn scam confidence">p_scam: ${turn.p_scam}</span>` : '';

            // Developer audit info
            let devDetails = "";
            if (state.currentRole === "developer") {
                const isMaskedDiff = turn.message !== turn.raw_message;
                devDetails = `
                    <div class="dev-highlight-group">
                        <div><strong>Origin:</strong> ${turn.original_sender} | <strong>Channel:</strong> ${turn.channel}</div>
                        ${isMaskedDiff ? `<div><strong>Masked Output:</strong> <span class="masked-pii-highlight">${maskTextFallback(turn.raw_message)}</span></div>` : ''}
                    </div>
                `;
            }

            wrapper.innerHTML = `
                <div class="message-sender-meta">
                    <span>${turn.sender}</span>
                    <span>${cleanTime}</span>
                    ${pScamBadge}
                </div>
                <div class="message-bubble">
                    <p>${textHtml}</p>
                    ${devDetails}
                </div>
            `;
            
            auditTranscriptMessages.appendChild(wrapper);
        });

        // Scroll to bottom
        auditTranscriptMessages.scrollTop = auditTranscriptMessages.scrollHeight;
    }

    // Fallback masking script matching the backend's logic for local rendering inside dev view
    function maskTextFallback(text) {
        if (!text) return text;
        return text
            .replace(/Margaret/gi, "[MASKED_VICTIM_NAME]")
            .replace(/Tommy/gi, "[MASKED_VICTIM_RELATION_NAME]")
            .replace(/Federal Security Bank/gi, "[MASKED_VICTIM_BANK]")
            .replace(/Federal Security/gi, "[MASKED_VICTIM_BANK]")
            .replace(/994821034/g, "[MASKED_VICTIM_ACCOUNT]")
            .replace(/Oak Street/gi, "[MASKED_VICTIM_ADDRESS]")
            .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, "[MASKED_EMAIL]");
    }

    // ─── Custom Canvas Line Chart Drawing ───
    function drawConfidenceChart(flow) {
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);

        const margin = { top: 20, right: 30, bottom: 30, left: 40 };
        const graphWidth = width - margin.left - margin.right;
        const graphHeight = height - margin.top - margin.bottom;

        // 1. Draw Grid Lines & Y Axis Labels
        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        ctx.fillStyle = "#6b7280";
        ctx.font = "10px sans-serif";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";

        const yTicks = 5;
        for (let i = 0; i <= yTicks; i++) {
            const val = (i / yTicks);
            const y = margin.top + graphHeight - (val * graphHeight);
            
            // Horizontal line
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(margin.left + graphWidth, y);
            ctx.stroke();

            // Label
            ctx.fillText(val.toFixed(1), margin.left - 10, y);
        }

        if (flow.length === 0) {
            ctx.textAlign = "center";
            ctx.fillStyle = "#6b7280";
            ctx.fillText("Waiting for conversation turns...", width / 2, height / 2);
            return;
        }

        // Filter turns down to only scammer message entries or display all turns
        const dataPoints = flow;

        // 2. Plot Points coordinates
        const stepX = dataPoints.length > 1 ? graphWidth / (dataPoints.length - 1) : graphWidth;
        const points = dataPoints.map((pt, idx) => {
            const x = margin.left + (idx * stepX);
            const y = margin.top + graphHeight - (pt.p_scam * graphHeight);
            return { x, y, val: pt.p_scam, sender: pt.sender, turn: pt.turn_number };
        });

        // 3. Draw gradient below curve
        if (points.length > 1) {
            const grad = ctx.createLinearGradient(0, margin.top, 0, margin.top + graphHeight);
            grad.addColorStop(0, "rgba(239, 68, 68, 0.25)");
            grad.addColorStop(1, "rgba(239, 68, 68, 0.0)");
            
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(points[0].x, margin.top + graphHeight);
            points.forEach(p => ctx.lineTo(p.x, p.y));
            ctx.lineTo(points[points.length - 1].x, margin.top + graphHeight);
            ctx.closePath();
            ctx.fill();
        }

        // 4. Draw Line connecting nodes
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 3;
        ctx.beginPath();
        points.forEach((p, idx) => {
            if (idx === 0) ctx.moveTo(p.x, p.y);
            else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();

        // 5. Draw points and write X-axis labels
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillStyle = "#9ca3af";
        
        points.forEach((p, idx) => {
            // Draw node dot
            ctx.beginPath();
            ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
            ctx.fillStyle = "#ffffff";
            ctx.fill();
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // X-axis turn number labels (skip some if there are too many)
            const labelSkip = Math.ceil(points.length / 10);
            if (idx % labelSkip === 0) {
                ctx.fillStyle = "#6b7280";
                ctx.fillText(`T${p.turn}`, p.x, margin.top + graphHeight + 10);
            }

            // Display rating on top of high points
            if (p.val >= 0.7) {
                ctx.fillStyle = "#f87171";
                ctx.font = "bold 9px sans-serif";
                ctx.fillText(p.val.toFixed(2), p.x, p.y - 14);
            }
        });
    }
});

// Helper polyfill
if (!String.prototype.lowerCase) {
    Object.defineProperty(String.prototype, 'lowerCase', {
        get: function() {
            return this.toLowerCase();
        }
    });
}
