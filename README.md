# SongGenAI

SongGenAI is a Django-based domain layer prototype for an AI song generation platform. This project focuses on modeling the core business entities and relationships of the system, including song generation requests, generated songs, libraries, sharing, users, and credit transactions.

This implementation was developed for **Exercise 3: Domain Layer Implementation Using Django**. The focus of this project is on **domain modeling and persistence** using Django ORM, rather than UI design or AI generation integration.

---

## Project Overview

The system supports the following core flow:

1. A **Creator** submits a **Form** as a song generation request.
2. The system creates a mock **Song** from that form.
3. Generated songs belong to the creator and represent the creator’s song history.
4. A creator can organize selected songs into one or more **Libraries**.
5. A song can be **shared** through a generated share token or link.
6. Credit usage is recorded through **CreditTransaction**.

---

## Main Features

- Django ORM domain modeling
- Data persistence with SQLite
- Relationships between domain entities
- Mock song generation from forms
- Song management and library organization
- Share token generation for songs
- Credit transaction tracking
- Django admin support for CRUD operations

---

## Domain Entities

The main domain entities in this project are:

- **Creator**
- **Listener**
- **Form**
- **Song**
- **Library**
- **Share**
- **CreditTransaction**

---

## Domain Relationships

The current design uses the following relationships:

- One **Creator** can have many **Forms**
- One **Creator** can have many **Songs**
- One **Creator** can have many **Libraries**
- One **Form** generates one **Song**
- One **Library** can contain many **Songs**
- One **Song** can belong to many **Libraries**
- One **Song** can have many **Shares**
- One **Creator** can have many **CreditTransactions**

---

## CRUD Functionality Explanation

CRUD functionality in this project was demonstrated using the **Django Admin panel**, which provides a simple interface for managing the implemented domain entities.

The following operations were tested:

### Create
New records were created for the main entities, including **Creator**, **Listener**, **Form**, **Song**, **Library**, **Share**, and **CreditTransaction**.

### Read
Stored records were viewed in the Django Admin panel to confirm that data was correctly saved in the database and that relationships between entities were properly maintained.

### Update
Existing records were modified through the admin interface, such as editing creator information, updating form details, changing song data, and modifying library contents.

### Delete
Records were deleted from the admin panel to verify that entities could be removed correctly from the database.

### Relationship Validation
The CRUD process also confirmed that the main domain relationships work as expected, such as:

- a **Creator** owning multiple **Forms**, **Songs**, **Libraries**, and **CreditTransactions**
- a **Form** generating a **Song**
- a **Library** containing multiple **Songs**
- a **Song** having multiple **Shares**

This demonstrates that the project supports the required persistence and basic CRUD operations for the domain layer implementation.

---

## Project Structure

```text
project_root/
├── app/
│   ├── controllers/
│   │   ├── generation_controller.py
│   │   ├── playback_controller.py
│   │   ├── song_manager_controller.py
│   │   └── user_controller.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── creator.py
│   │   ├── credit.py
│   │   ├── form.py
│   │   ├── library.py
│   │   ├── listener.py
│   │   ├── share.py
│   │   └── song.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── generation_urls.py
│   │   ├── manager_urls.py
│   │   ├── playback_urls.py
│   │   └── user_urls.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generation_service.py
│   │   ├── playback_service.py
│   │   ├── song_manager_service.py
│   │   └── user_service.py
│   │
│   ├── migrations/
│   │   └── ...
│   │
│   ├── admin.py
│   ├── apps.py
│   └── tests.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── .gitignore
├── LICENSE
├── manage.py
└── README.md
