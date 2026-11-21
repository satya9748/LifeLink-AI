
const $ = (id) => document.getElementById(id);

const connection = $("connection");

async function checkConnection() {
  try {
    await LifeLinkAPI.health();
    connection.textContent = "● API connected";
    connection.style.color = "#23875c";
  } catch {
    connection.textContent = "● API offline";
    connection.style.color = "#c43d49";
  }
}

// Escape HTML before displaying API data
function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}

// Display blood inventory
function renderInventory(items) {
  const target = $("inventoryResults");

  if (!items.length) {
    target.innerHTML =
      '<div class="empty-state">No matching released inventory was returned. This does not mean no blood exists elsewhere. Contact an authorized blood centre for urgent assistance.</div>';
    return;
  }

  target.innerHTML = `
    <div class="inventory-grid">
      ${items.map(item => `
        <article class="inventory-card">
          <b>${escapeHTML(item.blood_group)} · ${escapeHTML(item.component)}</b>
          <p>
            ${escapeHTML(item.blood_bank)}<br>
            ${escapeHTML(item.city)}<br>
            Unit reference: ${escapeHTML(item.unit_code)}<br>
            Recorded expiry: ${new Date(item.expiry_date).toLocaleDateString()}
          </p>
        </article>
      `).join("")}
    </div>
  `;
}

// Inventory search
$("searchForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const target = $("inventoryResults");
  target.innerHTML =
    '<div class="empty-state">Searching connected inventory...</div>';

  try {
    const params = {};

    if ($("city").value.trim()) {
      params.city = $("city").value.trim();
    }

    if ($("bloodGroup").value) {
      params.blood_group = $("bloodGroup").value;
    }

    const items = await LifeLinkAPI.inventory(params);
    renderInventory(items);
  } catch (error) {
    target.innerHTML = `
      <div class="empty-state">
        ${escapeHTML(error.message)}. Please check that the backend is running.
      </div>
    `;
  }
});

// Dialog elements
const loginDialog = $("loginDialog");
const registerDialog = $("registerDialog");

// Open login
$("loginOpen").addEventListener("click", () => {
  loginDialog.showModal();
});

// Open registration
$("registerOpen").addEventListener("click", () => {
  registerDialog.showModal();
});

// Switch from login to registration
$("switchToRegister").addEventListener("click", () => {
  loginDialog.close();
  registerDialog.showModal();
});

// Switch from registration to login
$("switchToLogin").addEventListener("click", () => {
  registerDialog.close();
  loginDialog.showModal();
});


// Dynamic registration fields
const registerRole = $("registerRole");

function updateRegistrationFields() {
  const role = registerRole.value;

  const groups = {
    donor: $("donorFields"),
    hospital: $("hospitalFields"),
    blood_bank: $("bloodBankFields")
  };

  const fieldIds = {
    donor: [
      "donorBloodGroup", "donorCity", "donorState", "donorPhone"
    ],
    hospital: [
      "hospitalName", "hospitalAddress", "hospitalCity",
      "hospitalState", "hospitalPhone"
    ],
    blood_bank: [
      "bloodBankName", "bloodBankLicense", "bloodBankAddress",
      "bloodBankCity", "bloodBankState", "bloodBankPhone"
    ]
  };

  Object.entries(groups).forEach(([key, element]) => {
    element.hidden = key !== role;
  });

  Object.entries(fieldIds).forEach(([key, ids]) => {
    ids.forEach(id => {
      $(id).required = key === role;
    });
  });
}

registerRole.addEventListener("change", updateRegistrationFields);
updateRegistrationFields();


// Registration form
$("registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = $("registerMessage");
  const submitButton = event.submitter;

  const fullName = $("registerName").value.trim();
  const email = $("registerEmail").value.trim();
  const password = $("registerPassword").value;
  const role = $("registerRole").value;

  message.textContent = "Creating your account...";
  submitButton.disabled = true;

  try {
    // 1. Create user account
    await LifeLinkAPI.register(fullName, email, password, role);

    message.textContent = "Account created. Setting up your profile...";

    // 2. Sign in automatically
    const loginResult = await LifeLinkAPI.login(email, password);

    localStorage.setItem("lifelink_token", loginResult.access_token);

    // 3. Create role-specific profile
    if (role === "donor") {
      await LifeLinkAPI.createDonor({
        blood_group: $("donorBloodGroup").value,
        city: $("donorCity").value.trim(),
        state: $("donorState").value.trim(),
        phone: $("donorPhone").value.trim(),
        consent_to_alerts: $("donorConsent").checked,
        available_for_contact: $("donorAvailable").checked
      });
    }

    else if (role === "hospital") {
      await LifeLinkAPI.createHospital({
        name: $("hospitalName").value.trim(),
        address: $("hospitalAddress").value.trim(),
        city: $("hospitalCity").value.trim(),
        state: $("hospitalState").value.trim(),
        phone: $("hospitalPhone").value.trim()
      });
    }

    else if (role === "blood_bank") {
      await LifeLinkAPI.createBloodBank({
        name: $("bloodBankName").value.trim(),
        license_number: $("bloodBankLicense").value.trim(),
        address: $("bloodBankAddress").value.trim(),
        city: $("bloodBankCity").value.trim(),
        state: $("bloodBankState").value.trim(),
        phone: $("bloodBankPhone").value.trim()
      });
    }

    message.textContent = "Registration and profile setup successful!";

    $("registerForm").reset();
    updateRegistrationFields();

    window.location.href = "dashboard.html";

  } catch (error) {
    message.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

// Login form
$("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = $("loginMessage");
    const submitButton = event.submitter;

    message.textContent = "Signing in...";
    submitButton.disabled = true;

    try {
        const result = await LifeLinkAPI.login(
            $("email").value.trim(),
            $("password").value
        );

        localStorage.setItem("lifelink_token", result.access_token);

        const user = await LifeLinkAPI.me();

        message.textContent =
    `Signed in as ${user.full_name} (${user.role}). Redirecting...`;

if (user.role === "admin") {
    window.location.href = "admin.html";
} else {
    window.location.href = "dashboard.html";
}
    } catch (error) {
        localStorage.removeItem("lifelink_token");
        message.textContent = error.message;

    } finally {
        submitButton.disabled = false;
    }
});

// Start API connection check
checkConnection();
