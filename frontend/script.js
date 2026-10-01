const API_URL = "";


// ========================================
// GET TOKEN
// ========================================

function getToken() {
    return localStorage.getItem("access_token");
}


// ========================================
// GET CURRENT USER
// ========================================

function getCurrentUser() {

    const user = localStorage.getItem("user");

    if (!user) {
        return null;
    }

    try {
        return JSON.parse(user);
    } catch (error) {
        return null;
    }
}


// ========================================
// CHECK ADMIN
// ========================================

function isAdmin() {

    const user = getCurrentUser();

    if (!user || !user.email) {
        return false;
    }

    return user.email.toLowerCase() === "preetam@gmail.com";
}


// ========================================
// AUTH HEADERS
// ========================================

function getAuthHeaders() {

    const token = getToken();

    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}


// ========================================
// REGISTER
// ========================================

async function register() {

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    const authMessage =
        document.getElementById("authMessage");


    if (!email || !password) {

        authMessage.innerText =
            "Please enter email and password.";

        return;
    }


    const name = prompt("Enter your name:");


    if (!name) {
        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/register`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password
                })
            }
        );


        const data = await response.json();


        if (response.ok) {

            authMessage.innerText =
                "Registration successful! Now click Login.";

            document.getElementById("password").value = "";

        } else {

            authMessage.innerText =
                data.detail || "Registration failed.";

        }

    } catch (error) {

        console.error(error);

        authMessage.innerText =
            "Could not connect to server.";

    }
}


// ========================================
// LOGIN
// ========================================

async function login() {

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    const authMessage =
        document.getElementById("authMessage");


    if (!email || !password) {

        authMessage.innerText =
            "Please enter email and password.";

        return;
    }


    try {

        console.log("Sending login request...");


        const response = await fetch(
            `${API_URL}/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })
            }
        );


        const data = await response.json();


        console.log("Login response:", data);


        if (!response.ok) {

            authMessage.innerText =
                data.detail || "Login failed.";

            return;
        }


        // Save JWT
        localStorage.setItem(
            "access_token",
            data.access_token
        );


        // Save user
        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );


        authMessage.innerText =
            "Login successful!";


        showAuthenticatedUI(data.user);


        loadBugs();

    } catch (error) {

        console.error(error);

        authMessage.innerText =
            "Could not connect to server.";

    }
}


// ========================================
// LOGOUT
// ========================================

function logout() {

    localStorage.removeItem("access_token");

    localStorage.removeItem("user");


    document.getElementById(
        "authSection"
    ).style.display = "block";


    document.getElementById(
        "userSection"
    ).style.display = "none";


    document.getElementById(
        "createBugSection"
    ).style.display = "none";


    document.getElementById(
        "filterSection"
    ).style.display = "none";


    document.getElementById(
        "bugSection"
    ).style.display = "none";


    document.getElementById(
        "authMessage"
    ).innerText =
        "Logged out.";
}


// ========================================
// SHOW USER UI
// ========================================

function showAuthenticatedUI(user) {

    document.getElementById(
        "authSection"
    ).style.display = "none";


    document.getElementById(
        "userSection"
    ).style.display = "block";


    document.getElementById(
        "filterSection"
    ).style.display = "block";


    document.getElementById(
        "bugSection"
    ).style.display = "block";


    document.getElementById(
        "userName"
    ).innerText = user.name;


    document.getElementById(
        "userRole"
    ).innerText = user.role;


    // ONLY PREETAM CAN CREATE BUG
    if (
        user.email &&
        user.email.toLowerCase() === "preetam@gmail.com"
    ) {

        document.getElementById(
            "createBugSection"
        ).style.display = "block";

    } else {

        document.getElementById(
            "createBugSection"
        ).style.display = "none";
    }
}


// ========================================
// CHECK LOGIN
// ========================================

async function checkAuthentication() {

    const token = getToken();


    if (!token) {
        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/me`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );


        if (!response.ok) {

            logout();

            return;
        }


        const data =
            await response.json();


        // Save latest user information
        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );


        showAuthenticatedUI(data.user);

        loadBugs();

    } catch (error) {

        console.error(error);

        logout();
    }
}


// ========================================
// LOAD BUGS
// ========================================

async function loadBugs() {

    const token = getToken();


    if (!token) {
        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/bugs`,
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );


        if (response.status === 401) {

            logout();

            return;
        }


        const data =
            await response.json();


        if (!response.ok) {

            console.error(data);

            return;
        }


        displayBugs(data.bugs);

    } catch (error) {

        console.error(error);
    }
}


// ========================================
// DISPLAY BUGS
// ========================================

function displayBugs(bugs) {

    const bugList =
        document.getElementById("bugList");


    bugList.innerHTML = "";


    if (!bugs || bugs.length === 0) {

        bugList.innerHTML =
            "<p>No bugs found.</p>";

        return;
    }


    bugs.forEach(bug => {

        const bugElement =
            document.createElement("div");


        bugElement.className = "bug";


        bugElement.innerHTML = `

            <h3>
                #${bug.id} - ${bug.title}
            </h3>

            <p>
                ${bug.description}
            </p>

            <p>
                <strong>Priority:</strong>
                ${bug.priority}
            </p>

            <p>
                <strong>Status:</strong>
                ${bug.status}
            </p>

            <p>
                <strong>Assigned to:</strong>
                ${bug.assigned_to || "Nobody"}
            </p>

            <p>
                <strong>Created by:</strong>
                ${bug.created_by || "Unknown"}
            </p>

        `;


        // ========================================
        // DELETE BUTTON - ADMIN ONLY
        // ========================================

        if (isAdmin()) {

            const deleteButton =
                document.createElement("button");

            deleteButton.innerText =
                "Delete Bug";

            deleteButton.style.background =
                "#dc2626";

            deleteButton.style.marginTop =
                "10px";

            deleteButton.onclick = function () {

                deleteBug(bug.id);

            };

            bugElement.appendChild(
                deleteButton
            );
        }


        bugList.appendChild(bugElement);

    });
}


// ========================================
// CREATE BUG
// ========================================

async function createBug() {

    const title =
        document.getElementById(
            "title"
        ).value.trim();


    const description =
        document.getElementById(
            "description"
        ).value.trim();


    const priority =
        document.getElementById(
            "priority"
        ).value;


    const assigned_to =
        document.getElementById(
            "assigned_to"
        ).value.trim();


    if (!title || !description) {

        alert(
            "Please enter title and description."
        );

        return;
    }


    const bug = {

        title: title,

        description: description,

        priority: priority,

        status: "open",

        assigned_to:
            assigned_to || null

    };


    try {

        const response = await fetch(
            `${API_URL}/bugs`,
            {
                method: "POST",

                headers: getAuthHeaders(),

                body: JSON.stringify(bug)
            }
        );


        const data =
            await response.json();


        if (response.status === 401) {

            logout();

            return;
        }


        if (response.status === 403) {

            alert(
                "You don't have permission."
            );

            return;
        }


        if (response.ok) {

            alert(
                "Bug created successfully!"
            );


            document.getElementById(
                "title"
            ).value = "";


            document.getElementById(
                "description"
            ).value = "";


            document.getElementById(
                "assigned_to"
            ).value = "";


            loadBugs();

        } else {

            alert(
                data.detail ||
                "Something went wrong."
            );
        }

    } catch (error) {

        console.error(error);

        alert(
            "Could not connect to server."
        );
    }
}


// ========================================
// DELETE BUG
// ========================================

async function deleteBug(bugId) {

    // Frontend protection
    if (!isAdmin()) {

        alert(
            "Only admin can delete bugs."
        );

        return;
    }


    // Confirmation
    const confirmed = confirm(
        `Are you sure you want to delete Bug #${bugId}?`
    );


    if (!confirmed) {
        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/bugs/${bugId}`,
            {
                method: "DELETE",

                headers: getAuthHeaders()
            }
        );


        const data =
            await response.json();


        // Token expired
        if (response.status === 401) {

            logout();

            return;
        }


        // Not admin
        if (response.status === 403) {

            alert(
                "Only admin can delete bugs."
            );

            return;
        }


        // Bug not found
        if (response.status === 404) {

            alert(
                "Bug not found."
            );

            loadBugs();

            return;
        }


        // Successful deletion
        if (response.ok) {

            alert(
                "Bug deleted successfully!"
            );

            loadBugs();

        } else {

            alert(
                data.detail ||
                "Failed to delete bug."
            );
        }

    } catch (error) {

        console.error(error);

        alert(
            "Could not connect to server."
        );
    }
}


// ========================================
// FILTER
// ========================================

function applyFilter() {

    loadBugs();
}


// ========================================
// BUTTON CONNECTIONS
// ========================================

document
    .getElementById("loginButton")
    .addEventListener("click", login);


document
    .getElementById("registerButton")
    .addEventListener("click", register);


document
    .getElementById("logoutButton")
    .addEventListener("click", logout);


document
    .getElementById("createBugButton")
    .addEventListener("click", createBug);


document
    .getElementById("filterButton")
    .addEventListener("click", applyFilter);


// ========================================
// START
// ========================================

console.log(
    "Bug Tracker JavaScript loaded!"
);

checkAuthentication();