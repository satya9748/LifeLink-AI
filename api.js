
window.LifeLinkAPI = {
  base: window.LIFELINK_CONFIG.API_BASE_URL,

  async request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    

    if (
      options.body &&
      !(options.body instanceof FormData) &&
      !(options.body instanceof URLSearchParams)
    ) {
      headers["Content-Type"] = "application/json";
    }

    const token = localStorage.getItem("lifelink_token");

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${this.base}${path}`, {
      ...options,
      headers
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || `Request failed (${response.status})`
      );
    }

    return data;
  },

  health() {
    return this.request("/health");
  },

  register(fullName, email, password, role) {
    return this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        role
      })
    });
  },

  login(email, password) {
    const body = new URLSearchParams({
      username: email,
      password
    });

    return this.request("/api/auth/login", {
      method: "POST",
      body
    });
  },

  me() {
    return this.request("/api/auth/me");
  },

  // Donor APIs
  createDonor(data) {
    return this.request("/api/donors", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  donorMe() {
    return this.request("/api/donors/me");
  },
updateDonorPreferences(data) {
  return this.request("/api/donors/me/preferences", {
    method: "PATCH",
    body: JSON.stringify(data)
  });
},


  // Hospital APIs
  createHospital(data) {
    return this.request("/api/hospitals", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  hospitalMe() {
    return this.request("/api/hospitals/me");
  },

  // Blood bank APIs
  createBloodBank(data) {
    return this.request("/api/blood-banks", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  bloodBankMe() {
    return this.request("/api/blood-banks/me");
  },

  // Inventory APIs
  inventory(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/api/inventory?${query.toString()}`);
  },

  myInventory() {
    return this.request("/api/inventory/my");
  },

  addBloodUnit(data) {
    return this.request("/api/inventory", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  // Hospital request APIs
  createBloodRequest(data) {
    return this.request("/api/requests", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  requests() {
    return this.request("/api/requests");
  },
matchInventory(requestId) {
  return this.request(`/api/requests/${requestId}/matches`);
},

updateRequestStatus(id, status) {
  return this.request(`/api/requests/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
},

// Admin APIs
adminBloodBanks() {
  return this.request("/api/admin/blood-banks");
},

updateBloodBankVerification(bankId, verified) {
  return this.request(
    `/api/admin/blood-banks/${bankId}/verification`,
    {
      method: "PATCH",
      body: JSON.stringify({ verified })
    }
  );
},
// Admin Blood Request Monitoring
adminBloodRequests() {
  return this.request("/api/admin/blood-requests");
},
// Admin Hospital APIs
adminHospitals() {
  return this.request("/api/admin/hospitals");
},

updateHospitalStatus(hospitalId, isActive) {
  return this.request(
    `/api/admin/hospitals/${encodeURIComponent(hospitalId)}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive })
    }
  );
},

// Admin Donor APIs
adminDonors() {
  return this.request("/api/admin/donors");
},
updateDonorStatus(donorId, isActive) {
  return this.request(
    `/api/admin/donors/${encodeURIComponent(donorId)}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive })
    }
  );
},

// Blood bank response APIs
availableBloodRequests() {
  return this.request("/api/blood-bank-responses/available-requests");
},

submitBloodBankResponse(data) {
  return this.request("/api/blood-bank-responses/", {
    method: "POST",
    body: JSON.stringify(data)
  });
},

  // Blood bank response APIs
  availableBloodRequests() {
    return this.request("/api/blood-bank-responses/available-requests");
  },

  submitBloodBankResponse(data) {
    return this.request("/api/blood-bank-responses/", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  myBloodBankResponses() {
  return this.request("/api/blood-bank-responses/my-responses");
},

  hospitalBloodBankResponses(requestId) {
    return this.request(
      `/api/blood-bank-responses/hospital/${requestId}`
    );
  }

};