# Role-Based Access Control (RBAC)

This document outlines the proposed access control for each user role in the B-Tree Admin Portal.

## 1. Admin

**Description:** Has full access to all modules and settings. Can manage users, courses, batches, students, payments, and all other aspects of the system.

**Permissions:**
- **User Management:** Create, Read, Update, Delete (CRUD) on all users.
- **Student Management:** CRUD on all students.
- **Batch Management:** CRUD on all batches.
- **Course Management:** CRUD on all courses.
- **Payment Management:** CRUD on all payments.
- **Placement Management:** CRUD on all placement records.
- **Consultant Management:** CRUD on all consultants.
- **Trainer Management:** CRUD on all trainers.
- **Settings:** Full access to all settings, including sources, payment accounts, and transaction logs.
- **Dashboards:** Access to all dashboards.

## 2. Staff

**Description:** General administrative staff who can manage core data like students, batches, and payments, but cannot manage users or system-level settings.

**Permissions:**
- **User Management:** No access.
- **Student Management:** CRUD on all students.
- **Batch Management:** CRUD on all batches.
- **Course Management:** Read-only access to courses.
- **Payment Management:** CRUD on all payments.
- **Placement Management:** Read-only access to placement records.
- **Consultant Management:** Read-only access to consultants.
- **Trainer Management:** Read-only access to trainers.
- **Settings:** No access.
- **Dashboards:** Access to staff and admin dashboards (read-only for admin).

## 3. Placement

**Description:** Responsible for managing student placements. Can view student and batch information and update placement records.

**Permissions:**
- **User Management:** No access.
- **Student Management:** Read-only access to all students.
- **Batch Management:** Read-only access to all batches.
- **Course Management:** No access.
- **Payment Management:** No access.
- **Placement Management:** CRUD on all placement records.
- **Consultant Management:** No access.
- **Trainer Management:** No access.
- **Settings:** No access.
- **Dashboards:** Access to a dedicated placement dashboard.

## 4. Trainer

**Description:** Can view information about the batches and students assigned to them.

**Permissions:**
- **User Management:** No access.
- **Student Management:** Read-only access to students in their assigned batches.
- **Batch Management:** Read-only access to their assigned batches.
- **Course Management:** No access.
- **Payment Management:** No access.
- **Placement Management:** No access.
- **Consultant Management:** No access.
- **Trainer Management:** Can view their own profile.
- **Settings:** No access.
- **Dashboards:** Access to a dedicated trainer dashboard.

## 5. Student

**Description:** Can view their own profile, course progress, and payment history.

**Permissions:**
- **User Management:** No access.
- **Student Management:** Can view their own profile.
- **Batch Management:** Can view their assigned batch details.
- **Course Management:** No access.
- **Payment Management:** Can view their own payment history.
- **Placement Management:** Can view their own placement status.
- **Consultant Management:** No access.
- **Trainer Management:** No access.
- **Settings:** No access.
- **Dashboards:** Access to a dedicated student dashboard.

## 6. Batch Coordination

**Description:** Responsible for creating and managing batches, including assigning trainers and students.

**Permissions:**
- **User Management:** No access.
- **Student Management:** Read-only access to all students.
- **Batch Management:** CRUD on all batches.
- **Course Management:** Read-only access to courses.
- **Payment Management:** No access.
- **Placement Management:** No access.
- **Consultant Management:** Read-only access to consultants.
- **Trainer Management:** Read-only access to trainers.
- **Settings:** No access.
- **Dashboards:** Access to a dedicated batch coordination dashboard.

## 7. Consultant

**Description:** Can view information about the students they have referred.

**Permissions:**
- **User Management:** No access.
- **Student Management:** Read-only access to students they have referred.
- **Batch Management:** No access.
- **Course Management:** No access.
- **Payment Management:** No access.
- **Placement Management:** No access.
- **Consultant Management:** Can view their own profile.
- **Trainer Management:** No access.
- **Settings:** No access.
- **Dashboards:** Access to a dedicated consultant dashboard.