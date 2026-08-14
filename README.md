## Resort Booking

A Frappe app for managing resort room inventory, guest bookings, advance
payments, pool/game-zone activity slots, and reception reporting.

Built for: Frappe Framework v15, no ERPNext dependency, no core modifications.

---

### 1. Installation

```bash
# from your bench directory
bench get-app resort_booking $URL_OF_THIS_REPO   # or unzip into apps/resort_booking
bench new-site your-site-name --db-root-password root
bench --site your-site-name install-app resort_booking
bench --site your-site-name migrate
```

Two roles are created automatically on install: **Resort Manager** and
**Receptionist**. Assign them to users from *User* > *Roles*.

Load the bundled sample data (rooms, rate plans, guests, bookings in every
status) with:

```bash
bench --site your-site-name execute resort_booking.data.import_sample_data.run
```

The dataset uses day-offsets from "today" rather than fixed dates, so it's
always relevant whenever you import it (see
`resort_booking/data/sample_data.json`).

---

### 2. Core flow

**Setup (Resort Manager):** Room Type → Room Category → Amenity → Room →
(optional) Rate Plan for seasonal pricing → Resort Resource (Pool/Game Zone).

**Taking a booking (Receptionist):**
1. Create a **Guest**.
2. Create a **Resort Booking**: pick the guest, check-in/check-out dates, and
   one or more rooms. Nightly rate, nights and grand total are calculated
   automatically (using any matching Rate Plan, falling back to the Room
   Type's default rate).
3. Set status to **Pre-booked** to hold the room for a configurable number of
   hours (default 24, see Resort Settings) without a payment. If it isn't
   confirmed in time, the scheduler cancels it automatically.
4. Record an advance payment via **Booking Payment** (type Advance). Once the
   advance reaches the configured minimum (default 30% of the grand total),
   the booking can be set to **Confirmed**.
5. On the day of arrival, set status to **Checked-in** - the room is marked
   Occupied automatically. On departure, set to **Checked-out** - the room is
   marked Available again.
6. **Cancelling** a booking (Resort Manager only) requires a reason and
   automatically creates a Refund-type Booking Payment for whatever advance
   was already paid, as a record of what's owed back to the guest.

**Status flow:** `Draft → Pre-booked → Confirmed → Checked-in → Checked-out`,
with `Cancelled` reachable from any state before Checked-in. The booking
enforces this order in code - it can't jump straight from Draft to
Checked-in, and can't be cancelled once the guest has already checked in.

**Activities (Story 4):** Create a **Resource Booking** for a Pool/Game Zone
slot, linked to the guest's Resort Booking. Slots are rejected if they fall
outside the resource's operating hours or if the resource is already at
capacity for that time.

---

### 3. Email settings

Go to **Resort Settings** (single doctype, search "Resort Settings" in the
awesomebar) to configure:

- **Minimum Advance Percent** - the advance % required to confirm a booking.
- **Pre-booking Hold Hours** - how long a Pre-booked hold lasts before it
  auto-cancels.
- **Management Alert Email** - receives an internal alert on every
  cancellation.
- **Email Templates** - one optional Email Template per notification
  (Booking Confirmation, Payment Receipt, Booking Cancellation, Pre-booking
  Reminder). If a template isn't set, a plain built-in message is sent
  instead, so email works out of the box with zero configuration.

Emails are sent via `frappe.sendmail()`, which requires a default outgoing
**Email Account** to actually leave the queue (*Settings > Email Account*).
Without one, emails are queued in the standard Frappe Email Queue and the
failure is written to the Error Log - a missing/misconfigured mail server
never blocks a booking or payment from going through.

---

### 4. Scheduler jobs

| Job | Frequency | What it does |
|---|---|---|
| `resort_booking.resort_booking.tasks.expire_pre_bookings` | Hourly | Cancels any Pre-booked reservation whose hold window has passed. |
| `resort_booking.resort_booking.tasks.send_prebooking_reminders` | Daily | Emails guests whose check-in is tomorrow. |

The scheduler must be enabled on the bench (`bench --site your-site-name
scheduler resume` if it was paused) for these to run automatically. You can
also trigger them by hand for testing:

```bash
bench --site your-site-name execute resort_booking.resort_booking.tasks.expire_pre_bookings
```

---

### 5. REST API (bonus)

Two whitelisted endpoints for availability checks, authenticated the same
way as any other Frappe API call (session cookie or `api_key:api_secret`):

```
GET /api/method/resort_booking.resort_booking.api.check_availability
    ?check_in=2026-09-01&check_out=2026-09-03&room_type=Luxury

GET /api/method/resort_booking.resort_booking.api.get_resource_slots
    ?resource=Main Pool&slot_date=2026-09-01
```

---

### 6. Reports & Workspace

Open the **Resort Booking** workspace for shortcuts, the booking calendar
(desk Calendar view on Resort Booking), and three reports:

- **Resort Occupancy Report** - room-nights booked vs. available, with a
  bar chart, for the last 6 months.
- **Todays Checkins** / **Todays Checkouts** - the day's arrivals/departures.

---

### 7. Permissions

| Doctype | Resort Manager | Receptionist |
|---|---|---|
| Room, Room Type, Room Category, Amenity, Rate Plan, Resort Resource | Full | Read only |
| Resort Booking | Full | Create/Read/Write (cannot cancel - enforced in code, not just doctype permissions) |
| Booking Payment | Full incl. Refund | Advance/Balance only (Refund is blocked in code) |
| Guest, Resource Booking | Full | Full |
| Resort Settings | Full | No access |

---

### 8. Running tests

```bash
bench --site your-site-name set-config allow_tests true
bench --site your-site-name run-tests --app resort_booking
```

Tests cover: pricing (including a stay that spans a Rate Plan boundary),
double-booking prevention, back-to-back same-day turnovers, the advance
payment gate, room status on check-in/check-out, blocking cancellation after
check-in, the automatic refund entry on cancellation, and resource slot
capacity/operating-hours checks.

### License

mit
