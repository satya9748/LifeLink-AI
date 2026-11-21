
document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("lifelink_token");

    if (!token) {
        window.location.href = "index.html";
        return;
    }

    try {
        const user = await LifeLinkAPI.me();

        if (user.role !== "admin") {
            alert("Access denied. Admin only.");
            window.location.href = "index.html";
            return;
        }

await loadBloodBanks();
await loadHospitals();
await loadDonors();
await loadBloodRequests();
    } catch (error) {
        alert("Session expired. Please log in again.");
        localStorage.removeItem("lifelink_token");
        window.location.href = "index.html";
    }
});

async function loadBloodBanks() {
    const table = document.getElementById("bloodBankTable");

    try {
        const banks = await LifeLinkAPI.adminBloodBanks();

        const total = banks.length;
        const verified = banks.filter(bank => bank.verified).length;
        const pending = total - verified;

        document.getElementById("totalBanks").textContent = total;
        document.getElementById("verifiedBanks").textContent = verified;
        document.getElementById("pendingBanks").textContent = pending;

        if (total === 0) {
            table.innerHTML = `
                <tr><td colspan="7">No blood banks registered.</td></tr>
            `;
            return;
        }

        table.innerHTML = banks.map(bank => `
            <tr>
                <td>${bank.id}</td>
                <td>${escapeHTML(bank.name)}</td>
                <td>${escapeHTML(bank.city)}</td>
                <td>${escapeHTML(bank.email)}</td>
                <td>${escapeHTML(bank.license_number)}</td>
                <td>
                    <span class="${bank.verified ? "verified" : "pending"}">
                        ${bank.verified ? "Verified" : "Pending"}
                    </span>
                </td>
                <td>
                    ${
                        bank.verified
                        ? `<button class="action-btn reject-btn"
                             onclick="changeVerification(${bank.id}, false)">
                             Revoke
                           </button>`
                        : `<button class="action-btn verify-btn"
                             onclick="changeVerification(${bank.id}, true)">
                             Verify
                           </button>`
                    }
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="7">${escapeHTML(error.message)}</td></tr>
        `;
    }
}

async function changeVerification(bankId, verified) {
    const action = verified ? "verify" : "revoke verification for";

    if (!confirm(`Are you sure you want to ${action} bank #${bankId}?`)) {
        return;
    }

    try {
        await LifeLinkAPI.updateBloodBankVerification(bankId, verified);

        alert("Blood bank verification updated successfully!");
        await loadBloodBanks();

    } catch (error) {
        alert("Error: " + error.message);
    }
}
// Load registered hospitals
async function loadHospitals() {
    const table = document.getElementById("hospitalTable");

    try {
        const hospitals = await LifeLinkAPI.adminHospitals();

        if (hospitals.length === 0) {
            table.innerHTML = `
                <tr><td colspan="7">No hospitals registered.</td></tr>
            `;
            return;
        }

        table.innerHTML = hospitals.map(hospital => `
            <tr>
                <td>${hospital.id}</td>
                <td>${escapeHTML(hospital.name)}</td>
                <td>${escapeHTML(hospital.city)}</td>
                <td>${escapeHTML(hospital.address)}</td>
                <td>${escapeHTML(hospital.phone)}</td>
                <td>
                    <span class="${hospital.is_active ? "verified" : "pending"}">
                        ${hospital.is_active ? "Active" : "Inactive"}
                    </span>
                </td>
                <td>
                    <button class="action-btn ${hospital.is_active ? "reject-btn" : "verify-btn"}"
                        onclick="changeHospitalStatus(${hospital.id}, ${!hospital.is_active})">
                        ${hospital.is_active ? "Deactivate" : "Activate"}
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="7">${escapeHTML(error.message)}</td></tr>
        `;
    }
}

// Activate or deactivate a hospital
async function changeHospitalStatus(hospitalId, isActive) {
    const action = isActive ? "activate" : "deactivate";

    if (!confirm(`Are you sure you want to ${action} hospital #${hospitalId}?`)) {
        return;
    }

    try {
        await LifeLinkAPI.updateHospitalStatus(hospitalId, isActive);

        alert(`Hospital ${action}d successfully!`);
        await loadHospitals();

    } catch (error) {
        alert("Error: " + error.message);
    }
}
// Load registered donors
async function loadDonors() {
    const table = document.getElementById("donorTable");

    try {
        const donors = await LifeLinkAPI.adminDonors();

        if (donors.length === 0) {
            table.innerHTML = `
                <tr><td colspan="8">No donors registered.</td></tr>
            `;
            return;
        }

        table.innerHTML = donors.map(donor => `
            <tr>
                <td>${donor.id}</td>
                <td>${escapeHTML(donor.name)}</td>
                <td>${escapeHTML(donor.email)}</td>
                <td>${escapeHTML(donor.blood_group)}</td>
                <td>${escapeHTML(donor.city)}</td>
                <td>${escapeHTML(donor.phone)}</td>
                <td>
                    <span class="${donor.is_active ? "verified" : "pending"}">
                        ${donor.is_active ? "Active" : "Inactive"}
                    </span>
                </td>
                <td>
                    <button
                        class="action-btn ${donor.is_active ? "reject-btn" : "verify-btn"}"
                        onclick="changeDonorStatus(${donor.id}, ${!donor.is_active})">
                        ${donor.is_active ? "Deactivate" : "Activate"}
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr><td colspan="8">${escapeHTML(error.message)}</td></tr>
        `;
    }
}

// Activate or deactivate a donor account
async function changeDonorStatus(donorId, isActive) {
    const action = isActive ? "activate" : "deactivate";

    if (!confirm(`Are you sure you want to ${action} donor #${donorId}?`)) {
        return;
    }

    try {
        await LifeLinkAPI.updateDonorStatus(donorId, isActive);

        alert(`Donor ${action}d successfully!`);
        await loadDonors();

    } catch (error) {
        alert("Error: " + error.message);
    }
}
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem("lifelink_token");
    window.location.href = "index.html";
});
// ==============================
// BLOOD REQUEST MONITORING
// ==============================

async function loadBloodRequests() {
    const table = document.getElementById("bloodRequestTable");

    try {
        const requests = await LifeLinkAPI.adminBloodRequests();

        if (!requests.length) {
            table.innerHTML = `
                <tr>
                    <td colspan="9">No blood requests found.</td>
                </tr>
            `;
            return;
        }

        table.innerHTML = requests.map(request => `
            <tr>
                <td>${request.id}</td>
                <td>${escapeHTML(request.hospital_name)}</td>
                <td>${escapeHTML(request.blood_group)}</td>
                <td>${escapeHTML(request.component)}</td>
                <td>${request.units_required}</td>
                <td>${escapeHTML(request.urgency)}</td>
                <td>${escapeHTML(request.city)}</td>
                <td>${escapeHTML(request.status)}</td>
                <td>${request.created_at
                    ? new Date(request.created_at).toLocaleString()
                    : "N/A"}
                </td>
            </tr>
        `).join("");

    } catch (error) {
        table.innerHTML = `
            <tr>
                <td colspan="9">${escapeHTML(error.message)}</td>
            </tr>
        `;
    }
}