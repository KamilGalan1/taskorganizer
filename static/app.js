// ======================
// SIDEBAR TOGGLE
// ======================


document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.querySelector('#sidebarToggle');
    const sidebar = document.querySelector('#sidebar');
    const content = document.querySelector('#content');

    if (sidebarToggle && sidebar && content) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            content.classList.toggle('shift');
        });
    } else {
        console.warn('Sidebar elements are missing. Check the HTML structure.');
    }
});




// ======================
// Task Management
// ======================

async function loadTasks() {
    const response = await fetch('/tasks', { method: 'GET' });
    if (response.ok) {
        const tasks = await response.json();
        renderTasks(tasks);
        updateStatistics(tasks);
    } else {
        console.error('Failed to load tasks:', response.status);
    }
}



function renderTasks(tasks) {
    console.log('Rendering tasks:', tasks); // Logowanie danych do konsoli
    const tasksDiv = document.getElementById('recently-added');

    // Wyczyść istniejące zadania
    tasksDiv.innerHTML = '';

    // Renderuj nowe zadania
    tasksDiv.innerHTML = tasks.map(task => `
        <div class="card mb-3 task-card" data-id="${task.id}">
            <div class="card-body">
                <h5 class="card-title">${task.title}</h5>
                <p class="card-text">${task.description.slice(0, 100)}${task.description.length > 100 ? '...' : ''}</p>
                <p class="card-text"><small>Due: ${task.due_date || 'No date'}</small></p>
                <p class="card-text"><span class="badge ${task.priority === 'High' ? 'bg-danger' : 'bg-secondary'}">${task.priority}</span></p>
                ${task.shared_by ? `
                    <p class="card-text shared-by">
                        <strong>Shared by:</strong> <span>${task.shared_by}</span>
                    </p>
                ` : ''}
                <button class="btn btn-sm mark-completed ${task.completed ? 'completed' : 'incomplete'}" data-id="${task.id}">
                    ${task.completed ? 'Mark as Incomplete' : 'Mark as Completed'}
                </button>
                <button class="btn btn-sm btn-danger delete-task" data-id="${task.id}">Delete</button>
            </div>
        </div>
    `).join('');



    document.querySelectorAll('.mark-completed').forEach(button => {
    button.addEventListener('click', async (e) => {
        e.stopPropagation(); // Zatrzymaj propagację
        const taskId = button.getAttribute('data-id');
        try {
            const response = await fetch(`/tasks/${taskId}/complete`, { method: 'PATCH' });
            if (response.ok) {
                const updatedTask = await response.json();
                // Znajdź kartę zadania i zaktualizuj jej stan
                const taskCard = document.querySelector(`.task-card[data-id="${taskId}"]`);
                if (taskCard) {
                    const statusButton = taskCard.querySelector('.mark-completed');
                    statusButton.textContent = updatedTask.completed ? 'Mark as Incomplete' : 'Mark as Completed';
                    statusButton.classList.toggle('completed', updatedTask.completed);
                    statusButton.classList.toggle('incomplete', !updatedTask.completed);
                }
            } else {
                console.error('Failed to update task status:', response.status);
            }
        } catch (error) {
            console.error('Error updating task status:', error);
        }
    });
});


   document.querySelectorAll('.task-card').forEach(card => {
    card.addEventListener('click', (e) => {
        // Upewnij się, że kliknięcie w „Delete” lub „Mark as Complete” nie otwiera edycji
        if (e.target.classList.contains('delete-task') || e.target.classList.contains('mark-completed')) {
            return;
        }
        const id = card.getAttribute('data-id');
        openEditForm(id); // Wywołaj formularz edycji.
    });
});


        document.querySelectorAll('.delete-task').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.stopPropagation(); // Zatrzymaj propagację, aby uniknąć przypadkowego otwierania edycji.
            const taskId = button.getAttribute('data-id');

            const activeFilterButton = document.querySelector('.filter-button.active');
            const activeFilter = activeFilterButton ? activeFilterButton.getAttribute('data-filter') : 'all';


            try {
                const response = await fetch(`/tasks/${taskId}`, { method: 'DELETE' });
                if (response.ok) {
                    loadFilteredTasks(activeFilter);
                calendar.refetchEvents(); // Odśwież wydarzenia w kalendarzu
                } else {
                    console.error('Failed to delete task:', response.status);
                }
            } catch (error) {
                console.error('Error deleting task:', error);
            }
        });
    });
}


// ======================
// Task Form
// ======================


document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const due_date = document.getElementById('due_date').value;
    const priority = document.getElementById('priority').value;

    const response = await fetch('/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, due_date, priority })
    });

    if (response.ok) {
        document.getElementById('task-form').reset();
        loadTasks(); // Odśwież listę zadań
        calendar.refetchEvents(); // Odśwież wydarzenia w kalendarzu
    } else {
        console.error('Failed to add task:', response.status);
    }
});






// ======================
// Edit Task Form Handling
// ======================


function openEditForm(taskId) {
    fetch(`/tasks/${taskId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch task');
            return response.json();
        })
        .then(task => {
            document.getElementById('recently-added').classList.add('d-none');
            document.getElementById('edit-task-section').classList.remove('d-none');

            document.getElementById('edit-task-id').value = task.id;
            document.getElementById('edit-title').value = task.title;
            document.getElementById('edit-due-date').value = task.due_date || '';
            document.getElementById('edit-description').value = task.description;
            document.getElementById('edit-priority').value = task.priority;

            // Zaktualizuj listę użytkowników
            sharedUsers = task.shared_with || [];
            renderSharedUsers();

            // Ukryj sekcję dodawania użytkowników, jeśli nie jesteś właścicielem
            const addUserSection = document.querySelector('.add-user-section');
            if (!task.is_owner) {
                addUserSection.style.display = 'none'; // Ukryj sekcję
            } else {
                addUserSection.style.display = 'block'; // Pokaż sekcję
            }

            handleEditFormSubmit(task.id); // Przekaż taskId do funkcji
        })
        .catch(err => console.error('Error fetching task:', err));
}


let sharedUsers = []; // Lista użytkowników

// Dodawanie użytkownika do listy
document.getElementById('add-user-btn').addEventListener('click', () => {
    const usernameInput = document.getElementById('shared-with-input');
    const username = usernameInput.value.trim();

    if (username && !sharedUsers.includes(username)) {
        sharedUsers.push(username); // Dodaj użytkownika do listy
        renderSharedUsers(); // Zaktualizuj wyświetlaną listę
        usernameInput.value = ''; // Wyczyść pole input
    }
});

// Przełączanie widoczności listy użytkowników
document.getElementById('toggle-user-list-btn').addEventListener('click', () => {
    const userListDiv = document.getElementById('shared-users-list');
    userListDiv.style.display = userListDiv.style.display === 'none' ? 'block' : 'none';
});

// Renderowanie listy użytkowników
function renderSharedUsers() {
    const sharedUsersList = document.getElementById('shared-users');
    sharedUsersList.innerHTML = ''; // Wyczyść listę

    sharedUsers.forEach(username => {
        const listItem = document.createElement('li');
        listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
        listItem.innerHTML = `
            ${username}
            <button type="button" class="btn btn-sm btn-outline-danger remove-user-btn" data-username="${username}">
                Remove
            </button>
        `;
        sharedUsersList.appendChild(listItem);
    });

    // Obsługa usuwania użytkowników
    document.querySelectorAll('.remove-user-btn').forEach(button => {
        button.addEventListener('click', () => {
            const username = button.getAttribute('data-username');
            sharedUsers = sharedUsers.filter(user => user !== username); // Usuń użytkownika z listy
            renderSharedUsers(); // Zaktualizuj wyświetlaną listę
        });
    });
}



function handleEditFormSubmit(taskId) {
    const editForm = document.getElementById('edit-task-form');

    editForm.onsubmit = async (e) => {
        e.preventDefault();

        const title = document.getElementById('edit-title').value;
        const description = document.getElementById('edit-description').value;
        const due_date = document.getElementById('edit-due-date').value;
        const priority = document.getElementById('edit-priority').value;

        console.log("Submitting the following data:", {
            title,
            description,
            due_date,
            priority,
            shared_with: sharedUsers.join(',')
        });

        try {
            const response = await fetch(`/tasks/${taskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    description,
                    due_date,
                    priority,
                    shared_with: sharedUsers.join(',') 
                })
            });

            if (response.ok) {
                alert('Task updated successfully!');
                window.location.href = '/homepage';
            } else {
                const error = await response.json();
                console.error('Error from server:', error);
                alert('Failed to update task. Check logs for more details.');
            }
        } catch (error) {
            console.error('Error during update:', error);
            alert('An error occurred while updating the task.');
        }
    };
}








// ======================
// TASK FILTER
// ======================

document.querySelectorAll('.filter-button').forEach(button => {
    button.addEventListener('click', () => {
        const filterType = button.getAttribute('data-filter');
        loadFilteredTasks(filterType); 
    });
});

async function loadFilteredTasks(filterType) {
    try {
        const response = await fetch(`/tasks/filter/${filterType}`);
        if (!response.ok) {
            console.error('Failed to load filtered tasks:', response.status);
            return;
        }

        const tasks = await response.json();
        console.log('Loaded tasks for filter:', filterType, tasks); // Logowanie danych
        renderTasks(tasks);
    } catch (error) {
        console.error('Error loading filtered tasks:', error);
    }
}


document.querySelectorAll('.filter-button').forEach(button => {
    button.addEventListener('click', function () {
        
        document.querySelectorAll('.filter-button').forEach(btn => btn.classList.remove('active'));

        
        this.classList.add('active');

       
        const filterType = this.getAttribute('data-filter');
        loadFilteredTasks(filterType);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const defaultFilter = 'all'; 
   
    document.querySelectorAll('.filter-button').forEach(button => {
        button.classList.remove('active');
        if (button.getAttribute('data-filter') === defaultFilter) {
            button.classList.add('active');
        }
    });

    loadFilteredTasks(defaultFilter);

   
    loadTasks();
    loadStatistics();
    fetchNotifications();
});

















// ======================
// SEARCH BAR
// ======================

document.getElementById('search-bar').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase(); // Pobierz i znormalizuj tekst wyszukiwania
    const taskCards = document.querySelectorAll('#recently-added .task-card'); // Pobierz wszystkie karty zadań

    taskCards.forEach((card) => {
        const title = card.querySelector('.card-title').textContent.toLowerCase();
        const description = card.querySelector('.card-text').textContent.toLowerCase();

        // Filtruj karty na podstawie tytułu lub opisu
        if (title.includes(searchTerm) || description.includes(searchTerm)) {
            card.style.display = ''; // Pokaż kartę
        } else {
            card.style.display = 'none'; // Ukryj kartę
        }
    });
});


document.getElementById('date-search-bar').addEventListener('input', (e) => {
    const searchDate = e.target.value; // Pobierz datę z paska wyszukiwania
    const taskCards = document.querySelectorAll('#recently-added .task-card'); // Pobierz wszystkie karty zadań

    taskCards.forEach((card) => {
        const dueDate = card.querySelector('.card-text small').textContent.replace('Due: ', '').trim();

        // Filtruj karty na podstawie daty wykonania
        if (dueDate === searchDate || searchDate === '') {
            card.style.display = ''; // Pokaż kartę
        } else {
            card.style.display = 'none'; // Ukryj kartę
        }
    });
});




// ======================
// CALENDAR SETUP
// ======================


let calendar;

        document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: async function(fetchInfo, successCallback, failureCallback) {
            try {
                const response = await fetch('/tasks');
                if (response.ok) {
                    const tasks = await response.json();
                    console.log('Loaded tasks for calendar:', tasks);
                    successCallback(tasks);
                } else {
                    console.error('Error fetching tasks for calendar:', response.status);
                    failureCallback('Failed to fetch tasks');
                }
            } catch (error) {
                console.error('Error loading tasks for calendar:', error);
                failureCallback(error);
            }
        },
        dayMaxEvents: 1, //  maksymalnie 1 wydarzenie na dzień


        moreLinkContent: function(args) {
            return `Zobacz jeszcze... ${args.num} tasków`; //  przycisk "zobacz jeszcze"
        },
        moreLinkClick: function(info) {
            
            const selectedDate = info.date.toISOString().split('T')[0]; // Format daty YYYY-MM-DD

            
            const dateSearchBar = document.getElementById('date-search-bar');
            if (dateSearchBar) {
                dateSearchBar.value = selectedDate;

                
                const inputEvent = new Event('input', { bubbles: true, cancelable: true });
                dateSearchBar.dispatchEvent(inputEvent);
            }

          
            const myTasksSection = document.getElementById('recently-added');
            if (myTasksSection) {
                myTasksSection.scrollIntoView({ behavior: 'smooth' }); 
            }

            
            return false;
        },
        dateClick: function(info) {
            openAddTaskForm(info.dateStr); 
        }
    });

    calendar.render();
});



        function openAddTaskForm(selectedDate) {
    const taskForm = document.getElementById('task-form');

    taskForm.reset(); 
    document.getElementById('due_date').value = selectedDate; 

   
    window.scrollTo({
        top: 0,
        behavior: 'smooth' 
    });

    const formCard = taskForm.closest('.card'); 
    formCard.classList.add('task-form-animate');

    
    setTimeout(() => {
        formCard.classList.remove('task-form-animate');
    }, 800); 
}





// ======================
// NOTIFICATIONS
// ======================

document.getElementById('notification-button').addEventListener('click', async () => {
    const dropdown = document.getElementById('notification-dropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';

    if (dropdown.style.display === 'block') {
        try {
            // Pobierz powiadomienia
            const response = await fetch('/notifications', { method: 'GET' });
            if (response.ok) {
                const notifications = await response.json();
                const list = document.getElementById('notification-list');
                list.innerHTML = notifications.length ? notifications.map(n => `
                    <li class="list-group-item ${n.read ? '' : 'bg-warning'}">
                        ${n.message} <small class="text-muted">${n.timestamp}</small>
                    </li>
                `).join('') : '<li class="list-group-item">No new notifications</li>';

                // Zresetuj licznik i oznacz jako przeczytane
                const markAsReadResponse = await fetch('/notifications/mark_all_as_read', { method: 'POST' });
                if (markAsReadResponse.ok) {
                    document.getElementById('notification-count').textContent = ''; // Zresetuj licznik
                }
            }
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        }
    }
});


        async function fetchNotifications() {
    try {
        const response = await fetch('/notifications/unread_count', { method: 'GET' });
        if (response.ok) {
            const data = await response.json();
            const count = data.unread_count;
            const notificationBadge = document.getElementById('notification-count');

            if (count > 0) {
                notificationBadge.textContent = count;
                notificationBadge.style.display = 'inline-block';
            } else {
                notificationBadge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error fetching unread notification count:', error);
    }
}

// Wywołaj fetchNotifications natychmiast po załadowaniu strony
document.addEventListener('DOMContentLoaded', () => {
    fetchNotifications(); // Pierwsze pobranie powiadomień od razu
    setInterval(fetchNotifications, 5000); // Następnie co 5 sekund
});





// ======================
// Load Initial Data
// ======================


        async function loadStatistics() {
    try {
        const response = await fetch('/tasks/statistics');
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('total-tasks').textContent = stats.total_tasks;
            document.getElementById('high-priority-tasks').textContent = stats.high_priority_tasks;
            document.getElementById('completed-tasks').textContent = stats.completed_tasks;
        } else {
            console.error('Failed to load statistics:', response.status);
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}


function updateStatistics(tasks) {
    const totalTasks = tasks.length;
    const highPriorityTasks = tasks.filter(task => task.priority === 'High').length;
    const completedTasks = tasks.filter(task => task.completed).length;

    // Aktualizuj statystyki na stronie
    document.getElementById('total-tasks').textContent = totalTasks;
    document.getElementById('high-priority-tasks').textContent = highPriorityTasks;
    document.getElementById('completed-tasks').textContent = completedTasks;
}



