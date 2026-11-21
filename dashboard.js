const $ = (id) => document.getElementById(id);

const content = $("dashboardContent");
const message = $("dashboardMessage");

let currentUser = null;

// -------------------------------
// COMMON HELPER FUNCTIONS
// -------------------------------

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}

function showMessage(text, isError = false) {
  if (!message) return;

  message.textContent = text;
  message.style.color = isError ? "#c43d49" : "#23875c";
}

function inputField(label, id, type = "text", required = true) {
  return `
    <label>
      ${escapeHTML(label)}
      <input id="${id}" type="${type}" ${required ? "required" : ""}>
    </label>
  `;
}

function selectField(label, id, options) {
  return `
    <label>
      ${escapeHTML(label)}
      <select id="${id}" required>
        <option value="">Select ${escapeHTML(label)}</option>
        ${options.map(option =>
          `<option value="${escapeHTML(option)}">${escapeHTML(option)}</option>`
        ).join("")}
      </select>
    </label>
  `;
}

function card(title, body) {
  return `
    <section class="dashboard-card">
      <h3>${escapeHTML(title)}</h3>
      ${body}
    </section>
  `;
}

function table(headers, rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return '<div class="empty-state">No records found yet.</div>';
  }

  return `
    <div class="dashboard-table-wrapper">
      <table class="dashboard-table">
        <thead>
          <tr>
            ${headers.map(h => `<th>${escapeHTML(h)}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => `
            <tr>
              ${row.map(value => `<td>${escapeHTML(value)}</td>`).join("")}
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function welcome(title, subtitle) {
  $("dashboardTitle").textContent = title;
  $("dashboardSubtitle").textContent = subtitle;

  return `
    <div class="dashboard-welcome">
      <div class="eyebrow">LIFELINK AI DASHBOARD</div>
      <h2>Welcome, ${escapeHTML(currentUser.full_name)}</h2>
      <p>${escapeHTML(subtitle)}</p>
      <span class="dashboard-badge">
        ${escapeHTML(currentUser.role.toUpperCase())}
      </span>
    </div>
  `;
}

function profileNotFound(error) {
  return error.message === "Hospital profile not found" ||
    error.message === "Donor profile not found" ||
    error.message === "Blood bank profile not found";
}

// -------------------------------
// DONOR DASHBOARD
// -------------------------------

async function loadDonorDashboard() {
  content.innerHTML = welcome(
    "Donor Dashboard",
    "Manage your donor profile and contact preferences."
  ) + '<div class="empty-state">Loading donor profile...</div>';

  try {
    const donor = await LifeLinkAPI.donorMe();

       content.innerHTML = welcome(
      "Donor Dashboard",
      "Manage your donor profile and contact preferences."
    ) + `
      <div class="dashboard-grid">

        ${card("My Donor Profile", `
          <p><b>Blood Group:</b> ${escapeHTML(donor.blood_group)}</p>
          <p><b>City:</b> ${escapeHTML(donor.city)}</p>
          <p><b>State:</b> ${escapeHTML(donor.state)}</p>
          <p><b>Phone:</b> ${escapeHTML(donor.phone)}</p>
        `)}

        ${card("Donor Consent & Availability", `
          <form id="donorPreferencesForm">
            <label class="checkbox-label">
              <input type="checkbox" id="donorConsent" ${donor.consent_to_alerts ? "checked" : ""}>
              I consent to receiving donor alerts.
            </label>

            <label class="checkbox-label">
              <input type="checkbox" id="donorAvailable" ${donor.available_for_contact ? "checked" : ""}>
              I am currently available for contact.
            </label>

            <button class="btn btn-primary" type="submit">
              Save Preferences
            </button>
          </form>
          <p><small>You can change these preferences at any time. Being available for contact does not establish medical eligibility to donate.</small></p>
        `)}

        ${card("Donor Information", `
          <p>Your profile helps authorized participating organizations contact you when additional donor support may be needed.</p>
          <p>Contact and donation eligibility must be confirmed separately by authorized professionals.</p>
        `)}

      </div>
    `;

    $("donorPreferencesForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = event.submitter;
      button.disabled = true;

      try {
        await LifeLinkAPI.updateDonorPreferences({
          consent_to_alerts: $("donorConsent").checked,
          available_for_contact: $("donorAvailable").checked
        });

        showMessage("Your donor preferences have been updated.");
      } catch (error) {
        showMessage(error.message, true);
      } finally {
        button.disabled = false;
      }
    });

  } catch (error) {
    if (!profileNotFound(error)) {
      showMessage(error.message, true);
      return;
    }
  // Load my blood bank response history
  let myResponses = [];

  try {
    const responseData = await LifeLinkAPI.myBloodBankResponses();
    myResponses = Array.isArray(responseData) ? responseData : [];
  } catch (error) {
    showMessage("Could not load response history: " + error.message, true);
  }
    content.innerHTML = welcome(
      "Donor Dashboard",
      "Complete your donor profile to join the network."
    ) + card("Create Donor Profile", `
      <form id="donorProfileForm">

        ${selectField("Blood Group", "donorBloodGroup",
          ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])}

        ${inputField("City", "donorCity")}
        ${inputField("State", "donorState")}
        ${inputField("Phone", "donorPhone", "tel")}

        <label class="checkbox-label">
          <input type="checkbox" id="donorConsent">
          I consent to receiving donor alerts.
        </label>

        <label class="checkbox-label">
          <input type="checkbox" id="donorAvailable">
          I am available for contact.
        </label>

        <button class="btn btn-primary" type="submit">
          Save Donor Profile
        </button>

      </form>
    `);

    $("donorProfileForm").addEventListener("submit", async (event) => {
      event.preventDefault();

      const button = event.submitter;
      button.disabled = true;

      try {
        await LifeLinkAPI.createDonor({
          blood_group: $("donorBloodGroup").value,
          city: $("donorCity").value.trim(),
          state: $("donorState").value.trim(),
          phone: $("donorPhone").value.trim(),
          consent_to_alerts: $("donorConsent").checked,
          available_for_contact: $("donorAvailable").checked
        });

        showMessage("Donor profile created successfully.");
        await loadDonorDashboard();

      } catch (err) {
        showMessage(err.message, true);
      } finally {
        button.disabled = false;
      }
    });
  }
}

// -------------------------------
// HOSPITAL DASHBOARD
// -------------------------------

async function loadHospitalDashboard() {
  content.innerHTML = welcome(
    "Hospital Dashboard",
    "Create blood requests and track their progress."
  ) + '<div class="empty-state">Loading hospital profile...</div>';

  let hospital;

  try {
    hospital = await LifeLinkAPI.hospitalMe();

  } catch (error) {
    if (!profileNotFound(error)) {
      showMessage(error.message, true);
      return;
    }

    content.innerHTML = welcome(
      "Hospital Dashboard",
      "Complete your hospital profile first."
    ) + card("Create Hospital Profile", `
      <form id="hospitalProfileForm">

        ${inputField("Hospital Name", "hospitalName")}
        ${inputField("Address", "hospitalAddress")}
        ${inputField("City", "hospitalCity")}
        ${inputField("State", "hospitalState")}
        ${inputField("Phone", "hospitalPhone", "tel")}

        <button class="btn btn-primary" type="submit">
          Save Hospital Profile
        </button>

      </form>
    `);

    $("hospitalProfileForm").addEventListener("submit", async (event) => {
      event.preventDefault();

      const button = event.submitter;
      button.disabled = true;

      try {
        await LifeLinkAPI.createHospital({
          name: $("hospitalName").value.trim(),
          address: $("hospitalAddress").value.trim(),
          city: $("hospitalCity").value.trim(),
          state: $("hospitalState").value.trim(),
          phone: $("hospitalPhone").value.trim()
        });

        showMessage("Hospital profile created successfully.");
        await loadHospitalDashboard();

      } catch (err) {
        showMessage(err.message, true);
      } finally {
        button.disabled = false;
      }
    });

    return;
  }

  // Load hospital requests
  let requests = [];

  try {
    const requestData = await LifeLinkAPI.requests();
    requests = Array.isArray(requestData) ? requestData : [];

  } catch (error) {
    showMessage(error.message, true);
  }
// Load blood bank responses for each request
const bankResponses = {};

await Promise.all(
  requests.map(async (request) => {
    try {
      bankResponses[request.id] =
        await LifeLinkAPI.hospitalBloodBankResponses(request.id);
    } catch (error) {
      bankResponses[request.id] = {
        error: error.message,
        responses: []
      };
    }
  })
);
  // Load inventory matches for each request
  const matchResults = {};

  await Promise.all(
    requests.map(async (request) => {
      try {
       matchResults[request.id] =
  await LifeLinkAPI.matchInventory(request.id);


      } catch (error) {
       matchResults[request.id] = {
  error: error.message
};
      }
    })
  );

  // Display hospital dashboard
  content.innerHTML = welcome(
    "Hospital Dashboard",
    "Create blood requests and track their progress."
  ) + `

    <div class="dashboard-grid">

      ${card("Hospital Profile", `
        <p><b>Name:</b> ${escapeHTML(hospital.name)}</p>
        <p><b>City:</b> ${escapeHTML(hospital.city)}</p>
        <p><b>State:</b> ${escapeHTML(hospital.state)}</p>
        <p><b>Phone:</b> ${escapeHTML(hospital.phone)}</p>
      `)}

      ${card("Create Blood Request", `
        <form id="bloodRequestForm">

          ${selectField("Blood Group", "requestGroup",
            ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])}

          ${selectField("Component", "requestComponent",
            ["Whole Blood", "Packed Red Blood Cells", "Platelets", "Plasma", "Cryoprecipitate"])}

          ${inputField("Units Required", "requestUnits", "number")}

          ${selectField("Urgency", "requestUrgency",
            ["normal", "urgent", "emergency"])}

          ${inputField("City", "requestCity")}

          ${inputField("Clinical Reference (optional)", "clinicalReference", "text", false)}

          <button class="btn btn-primary" type="submit">
            Submit Blood Request
          </button>

        </form>
      `)}

    </div>

    ${card("My Blood Requests", table(
      ["ID", "Blood Group", "Component", "Units", "Urgency", "Status"],
      requests.map(r => [
       r.id,
        r.blood_group,
        r.component,
        r.units_required,
        r.urgency,
        r.status
      ])
    ))}

    ${card("Automatic Inventory Matching", requests.length ? `

      ${requests.map(r => {

        const result = matchResults[r.id];

        if (!result) {
          return `<p>Request #${escapeHTML(r.id)}: Loading matches...</p>`;
        }

        if (result.error) {
          return `
            <p>
              Request #${escapeHTML(r.request_id)}:
              ${escapeHTML(result.error)}
            </p>
          `;
        }

        const matches = Array.isArray(result.matches)
          ? result.matches
          : [];
    const responseData = bankResponses[r.id];

const responses = responseData && Array.isArray(responseData.responses)
  ? responseData.responses
  : [];

        return `

          <div class="dashboard-card">

            <h4>Request #${escapeHTML(r.request_id)}</h4>

            <p>
              <b>Required:</b>
              ${escapeHTML(result.units_required)} units
            </p>

            <p>
              <b>Matching units:</b>
              ${escapeHTML(result.matching_units)}
            </p>

            <p>
              <b>Quantity satisfied:</b>
              ${result.quantity_satisfied ? "Yes" : "No"}
            </p>

            ${matches.length ? table(
              ["Blood Bank", "City", "Unit Code", "Expiry", "Location Match"],
              matches.map(unit => [
                unit.blood_bank,
                unit.city,
                unit.unit_code,
                unit.expiry_date
                  ? new Date(unit.expiry_date).toLocaleDateString()
                  : "—",
                unit.location_match ? "Yes" : "No"
              ])
            ) : `
              <p>No matching released inventory found.</p>
            `}
<div class="bank-responses">
  <h4>Blood Bank Responses</h4>

  ${responseData?.error
    ? `<p>Could not load responses: ${escapeHTML(responseData.error)}</p>`
    : responses.length
      ? responses.map(response => `
          <div class="dashboard-card">
            <p><b>Blood Bank:</b> ${escapeHTML(response.blood_bank_name || "Name unavailable")}</p>
            <p><b>Status:</b> ${escapeHTML(response.response_status.toUpperCase())}</p>
            <p><b>Units Offered:</b> ${escapeHTML(response.units_offered)}</p>
            <p><b>Message:</b> ${escapeHTML(response.response_message || "No message provided")}</p>
            <p><b>Responded At:</b> ${escapeHTML(response.responded_at || "Not available")}</p>
          </div>
        `).join("")
      : "<p>No blood bank responses received yet.</p>"
  }
</div>
            <p>${escapeHTML(result.message)}</p>

            <p>
              <small>${escapeHTML(result.clinical_notice)}</small>
            </p>

          </div>

        `;

      }).join("")}

    ` : "<p>Submit a blood request to see matching results.</p>")}

  `;

  // Submit blood request
  $("bloodRequestForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = event.submitter;
    button.disabled = true;

    try {
      await LifeLinkAPI.createBloodRequest({
        blood_group: $("requestGroup").value,
        component: $("requestComponent").value,
        units_required: Number($("requestUnits").value),
        urgency: $("requestUrgency").value,
        city: $("requestCity").value.trim(),
        clinical_reference: $("clinicalReference").value.trim() || null
      });

      showMessage("Blood request submitted successfully.");
      await loadHospitalDashboard();

    } catch (err) {
      showMessage(err.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

// -------------------------------
// BLOOD BANK DASHBOARD
// -------------------------------

async function loadBloodBankDashboard() {
  content.innerHTML = welcome(
    "Blood Bank Dashboard",
    "Manage your blood bank profile, inventory and hospital requests."
  ) + '<div class="empty-state">Loading blood bank dashboard...</div>';

  let bank;
  let myResponses = [];

  try {
    bank = await LifeLinkAPI.bloodBankMe();

  } catch (error) {
    if (!profileNotFound(error)) {
      showMessage(error.message, true);
      return;
    }
  // Load my blood bank response history
  


    content.innerHTML = welcome(
      "Blood Bank Dashboard",
      "Register your blood bank details."
    ) + card("Create Blood Bank Profile", `
      <form id="bankProfileForm">

        ${inputField("Blood Bank Name", "bankName")}
        ${inputField("License Number", "bankLicense")}
        ${inputField("Address", "bankAddress")}
        ${inputField("City", "bankCity")}
        ${inputField("State", "bankState")}
        ${inputField("Phone", "bankPhone", "tel")}

        <button class="btn btn-primary" type="submit">
          Submit Bank Profile
        </button>

      </form>
    `);

    $("bankProfileForm").addEventListener("submit", async (event) => {
      event.preventDefault();

      const button = event.submitter;
      button.disabled = true;

      try {
        await LifeLinkAPI.createBloodBank({
          name: $("bankName").value.trim(),
          license_number: $("bankLicense").value.trim(),
          address: $("bankAddress").value.trim(),
          city: $("bankCity").value.trim(),
          state: $("bankState").value.trim(),
          phone: $("bankPhone").value.trim()
        });

        showMessage("Blood bank profile submitted for verification.");
        await loadBloodBankDashboard();

      } catch (err) {
        showMessage(err.message, true);
      } finally {
        button.disabled = false;
      }
    });

    return;
  }
  // Load my blood bank response history
  try {
    const responseData = await LifeLinkAPI.myBloodBankResponses();
    myResponses = Array.isArray(responseData) ? responseData : [];
  } catch (error) {
    showMessage("Could not load response history: " + error.message, true);
  }
  let units = [];
  let requests = [];

  try {
    const inventoryData = await LifeLinkAPI.myInventory();
    units = Array.isArray(inventoryData) ? inventoryData : [];

  } catch (error) {
    showMessage(error.message, true);
  }

  try {
    const requestData = await LifeLinkAPI.availableBloodRequests();
requests = Array.isArray(requestData) ? requestData : [];

  } catch (error) {
    showMessage("Could not load hospital requests: " + error.message, true);
  }

  content.innerHTML = welcome(
    "Blood Bank Dashboard",
    "Manage your blood bank profile, inventory and hospital requests."
  ) + `

    <div class="dashboard-grid">

      ${card("Blood Bank Profile", `
        <p><b>Name:</b> ${escapeHTML(bank.name)}</p>
        <p><b>License:</b> ${escapeHTML(bank.license_number)}</p>
        <p><b>City:</b> ${escapeHTML(bank.city)}</p>
        <p><b>State:</b> ${escapeHTML(bank.state)}</p>
        <p><b>Verification:</b>
          ${bank.verified ? "Verified" : "Pending verification"}
        </p>
      `)}

      ${card("Add Blood Unit", `
        <form id="addUnitForm">

          ${inputField("Unit Code", "unitCode")}

          ${selectField("Blood Group", "unitGroup",
            ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])}

          ${selectField("Component", "unitComponent",
            ["Whole Blood", "Packed Red Blood Cells", "Platelets", "Plasma", "Cryoprecipitate"])}

          ${inputField("Collection Date", "collectionDate", "datetime-local")}

          ${inputField("Expiry Date", "expiryDate", "datetime-local")}

          <button class="btn btn-primary" type="submit">
            Add Blood Unit
          </button>

        </form>

        <p>
          New units remain quarantined until authorized staff complete
          screening and release.
        </p>
      `)}

    </div>

    ${card("My Blood Inventory", table(
      ["Unit Code", "Blood Group", "Component", "Screening", "Status", "Expiry"],
      units.map(u => [
        u.unit_code,
        u.blood_group,
        u.component,
        u.screening_status,
        u.status,
        u.expiry_date
          ? new Date(u.expiry_date).toLocaleDateString()
          : "—"
      ])
    ))}
   ${card("My Response History", `
     ${myResponses.length ? myResponses.map(response => `
       <div class="dashboard-card">
         <h4>Request #${escapeHTML(response.request_id)}</h4>

         <p>
           <strong>Status:</strong>
           ${escapeHTML(response.response_status.toUpperCase())}
         </p>

         <p>
           <strong>Units Offered:</strong>
           ${escapeHTML(response.units_offered)}
         </p>

         <p>
           <strong>Message:</strong>
           ${escapeHTML(response.response_message || "No message provided")}
         </p>

         <p>
           <strong>Responded At:</strong>
           ${escapeHTML(response.responded_at || "Not available")}
         </p>
       </div>
     `).join("") : `
       <div class="empty-state">
         You have not submitted any responses yet.
       </div>
     `}
   `)}
   ${card("Incoming Hospital Requests", `

  <p>Review requests submitted by participating hospitals.</p>

  ${requests.length ? requests.map(r => `
    <div class="dashboard-card">
      <h4>Request #${escapeHTML(r.request_id)}</h4>

      <p>
        <strong>Blood Group:</strong> ${escapeHTML(r.blood_group)} |
        <strong>Component:</strong> ${escapeHTML(r.component)}
      </p>

      <p>
        <strong>Units Required:</strong> ${escapeHTML(r.units_required)} |
        <strong>Urgency:</strong> ${escapeHTML(r.urgency)}
      </p>

      <p><strong>City:</strong> ${escapeHTML(r.city)}</p>

      <label for="offerUnits-${escapeHTML(r.request_id)}">
        Units you can offer
      </label>

      <input
        type="number"
        id="offerUnits-${escapeHTML(r.request_id)}"
        min="1"
        max="${escapeHTML(r.units_required)}"
        value="1"
      >

      <label for="offerMessage-${escapeHTML(r.request_id)}">
        Response message (optional)
      </label>

      <input
        type="text"
        id="offerMessage-${escapeHTML(r.request_id)}"
        placeholder="Enter a message for the hospital"
      >

      <button
        class="btn btn-primary respond-request"
        type="button"
        data-id="${escapeHTML(r.request_id)}"
        data-response="accepted">
        Accept Request
      </button>

      <button
        class="btn btn-outline respond-request"
        type="button"
        data-id="${escapeHTML(r.request_id)}"
        data-response="declined">
        Decline Request
      </button>
    </div>
  `).join("") : `
    <div class="empty-state">
      No matching hospital requests are currently available.
    </div>
  `}

  <p>
    <strong>Important:</strong> Accepting a request is an offer only.
    It does not reserve or issue blood units.
  </p>

`)}

  `;

  // Add blood unit
  $("addUnitForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = event.submitter;
    button.disabled = true;

    try {
      const collectionDate = $("collectionDate").value;
      const expiryDate = $("expiryDate").value;

      if (!collectionDate || !expiryDate) {
        throw new Error("Please enter both collection and expiry dates.");
      }

      if (new Date(expiryDate) <= new Date(collectionDate)) {
        throw new Error("Expiry date must be later than collection date.");
      }

      await LifeLinkAPI.addBloodUnit({
        unit_code: $("unitCode").value.trim(),
        blood_group: $("unitGroup").value,
        component: $("unitComponent").value,
        collection_date: new Date(collectionDate).toISOString(),
        expiry_date: new Date(expiryDate).toISOString(),
        screening_status: "pending"
      });

      showMessage("Blood unit recorded in quarantine.");
      await loadBloodBankDashboard();

    } catch (err) {
      showMessage(err.message, true);
    } finally {
      button.disabled = false;
    }
  });

  // Blood bank response handling
  document.querySelectorAll(".respond-request").forEach(button => {

    button.addEventListener("click", async () => {

      const requestId = Number(button.dataset.id);
      const responseStatus = button.dataset.response;

      const unitsInput = $("offerUnits-" + requestId);
      const messageInput = $("offerMessage-" + requestId);

      const unitsOffered = responseStatus === "accepted"
        ? Number(unitsInput.value)
        : 0;

      if (responseStatus === "accepted" && unitsOffered < 1) {
        showMessage("Please enter at least one unit.", true);
        return;
      }

      const responseMessage = messageInput.value.trim();

      button.disabled = true;

      try {
        await LifeLinkAPI.submitBloodBankResponse({
          request_id: requestId,
          response_status: responseStatus,
          units_offered: unitsOffered,
          response_message: responseMessage || null
        });

        showMessage(
          `Your ${responseStatus} response was submitted successfully.`
        );

        await loadBloodBankDashboard();

      } catch (error) {
        showMessage(error.message, true);
      } finally {
        button.disabled = false;
      }

    });

  });
}
// -------------------------------
// GMAIL INBOX PANEL
// -------------------------------

async function loadGmailPanel() {
  content.insertAdjacentHTML("beforeend", `
    <section class="dashboard-card" id="gmailPanel">
      <h3>📧 My Gmail Inbox</h3>
      <p id="gmailStatus">Loading Gmail messages...</p>
      <button class="btn btn-primary" id="refreshGmail">
        Refresh Inbox
      </button>
      <div id="gmailMessages"></div>
    </section>
  `);

  const status = $("gmailStatus");
  const messagesBox = $("gmailMessages");
  const refreshButton = $("refreshGmail");

  async function refreshInbox() {
    refreshButton.disabled = true;
    status.textContent = "Loading messages...";

    try {
            const data = await LifeLinkAPI.request(
        "/api/gmail/inbox?max_results=20"
      );

      const emails = data.messages || [];

      status.textContent = `${emails.length} messages loaded`;

      if (!emails.length) {
        messagesBox.innerHTML =
          '<div class="empty-state">Your inbox is empty.</div>';
        return;
      }

      messagesBox.innerHTML = emails.map(email => `
        <div class="dashboard-card">
          <p><strong>${escapeHTML(email.subject)}</strong>
          ${email.unread ? '<span class="dashboard-badge">Unread</span>' : ''}</p>
          <p><strong>From:</strong> ${escapeHTML(email.sender)}</p>
          <p><strong>Date:</strong> ${escapeHTML(email.date)}</p>
          <p>${escapeHTML(email.snippet)}</p>
        </div>
      `).join("");

    } catch (error) {
      status.textContent = error.message;
      messagesBox.innerHTML = "";
    } finally {
      refreshButton.disabled = false;
    }
  }

  refreshButton.addEventListener("click", refreshInbox);
  await refreshInbox();
}
// -------------------------------
// LOGIN AND ROLE PROTECTION
// -------------------------------

async function initializeDashboard() {

  const token = localStorage.getItem("lifelink_token");

  if (!token) {
    window.location.replace("index.html");
    return;
  }

  try {

    currentUser = await LifeLinkAPI.me();

    $("userName").textContent = currentUser.full_name;

    if (currentUser.role === "donor") {

      await loadDonorDashboard();

    } else if (currentUser.role === "hospital") {

      await loadHospitalDashboard();

    } else if (currentUser.role === "blood_bank") {

      await loadBloodBankDashboard();

    } else {

      showMessage("This account does not have a dashboard.", true);

    }
    await loadGmailPanel();
 } catch (error) {

  console.error("Dashboard initialization error:", error);

  showMessage(
    "Dashboard loading failed: " + error.message,
    true
  );

}

}

// -------------------------------
// LOGOUT
// -------------------------------

if ($("logoutButton")) {

  $("logoutButton").addEventListener("click", () => {

    localStorage.removeItem("lifelink_token");
    window.location.replace("index.html");

  });

}

// Start dashboard
initializeDashboard();