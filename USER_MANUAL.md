# Resort Booking - User Manual

This guide is for the people who use the app day to day: the **Resort
Manager** (sets up the property, manages pricing and settings, approves
cancellations/refunds) and the **Receptionist** (takes bookings, records
payments, checks guests in and out).

Everything is accessed from the **Resort Booking** workspace after logging
into the desk (`/app/resort-booking`).

---

## 1. Setting up the property (Resort Manager)

Do this once, before taking any bookings.

1. **Room Type** - create one record per tier: Luxury, Medium, Normal,
   Dormitory. Set a **Default Rate Per Night** for each - this is the price
   used whenever no special Rate Plan applies.
2. **Room Category** - create one per area: Heritage, Cottages, Villas, Game
   Zone, Pool Cabanas.
3. **Amenity** - create one per amenity you offer: Wi-Fi, Pool Access, AC,
   TV, Mini Bar, etc.
4. **Room** - one record per physical room. Set its Room Number, Room Type,
   Room Category, current Status (Available / Occupied / Under Maintenance),
   and tick off its Amenities.
5. *(Optional)* **Rate Plan** - if a Room Type should charge a different rate
   for a season or festival period, create a Rate Plan: pick the Room Type, a
   From/To date range, and the rate for those nights. A booking that spans
   the edge of a Rate Plan is priced night-by-night automatically - no manual
   splitting needed.
6. *(Optional)* **Resort Resource** - for the pool, game zone, or any other
   shared facility guests book time slots for. Set its Capacity (how many
   slots can run at once) and Operating Hours.
7. **Resort Settings** - open this once and check the Minimum Advance
   Percent (default 30%) and Pre-booking Hold Hours (default 24) match your
   policy. Set the Management Alert Email so you're notified of
   cancellations.

---

## 2. Taking a booking (Receptionist)

1. Open **Guest** and create the guest if they're new (name, phone, email,
   ID proof are enough).
2. Open **Resort Booking** > New.
3. Select the **Guest**, the **Check-in** and **Check-out** dates, and add
   one or more rooms in the **Rooms** table.
4. Save. The system fills in **Total Nights**, **Grand Total**, and the
   **Minimum Advance Required** for you - you don't calculate these by hand.
5. If the guest wants to hold the room without paying yet, set **Status** to
   **Pre-booked** and save. The room is held for the number of hours set in
   Resort Settings (default 24) - after that it cancels itself and the room
   becomes available again, even if nobody touches it.
6. To actually secure the booking, record the guest's advance payment first
   (see next section), then set **Status** to **Confirmed** and save. If the
   advance paid so far is below the required minimum, the system will stop
   you and tell you exactly how much more is needed.

**Trying to book a room that's already taken for those dates?** The system
will block the save and tell you which existing booking is in the way. This
happens automatically - you don't need to check availability by hand first
(though you can, via the Calendar view - see section 5).

---

## 3. Recording payments

1. Open **Booking Payment** > New.
2. Select the **Booking**, choose the **Payment Type** (Advance or Balance),
   enter the **Amount** and **Payment Mode**, then **Submit**.
3. The parent booking's Advance Paid and Balance Due update automatically -
   you don't edit those fields yourself, they're read-only and always
   reflect the sum of submitted payments.
4. A payment receipt email is sent to the guest automatically on submit (see
   section 6 on email).

**Refunds** can only be recorded by a Resort Manager, and in most cases you
won't need to create one by hand - cancelling a booking that already had an
advance paid creates the refund entry automatically (see next section).

---

## 4. Check-in, check-out and cancellation

- **Check-in**: on the Resort Booking, set Status to **Checked-in**. The
  room's status flips to *Occupied* automatically.
- **Check-out**: set Status to **Checked-out**. The room flips back to
  *Available* automatically, ready for the next guest.
- **Cancellation** (Resort Manager only): set Status to **Cancelled** and
  fill in the Cancellation Reason. If any advance was paid, a Refund entry is
  created for you automatically under Booking Payment, so nothing has to be
  tracked separately. Once a guest has checked in, a booking can no longer be
  cancelled - at that point you'd check them out instead.

---

## 5. Checking availability and the calendar

- The **Resort Booking** list has a **Calendar** view (switch view from the
  top-right of the list) showing every booking by check-in/check-out date -
  useful for a quick visual of who's arriving and leaving when.
- The workspace has **Todays Checkins** and **Todays Checkouts** reports for
  a same-day operational view.
- The **Resort Occupancy Report** (workspace > Reports) shows a bar chart of
  occupancy % for the last 6 months, based on rooms actually sold
  (Confirmed/Checked-in/Checked-out bookings) versus total room-nights
  available.

---

## 6. Automated emails

The app sends an email automatically at each of these points - no manual
action needed:

| Trigger | Sent to |
|---|---|
| Booking set to Confirmed | Guest |
| Payment submitted (Advance/Balance) | Guest |
| Booking Cancelled | Guest + the Management Alert Email address |
| 24 hours before check-in | Guest |

To change the wording, go to **Resort Settings** and link an **Email
Template** for the trigger you want to customize (Settings > Email Template
to create one). Leave it blank to keep the plain built-in message.

If no outgoing email account is configured for the site, emails won't
actually leave the server, but nothing else in the app is affected - the
booking or payment still goes through normally.

---

## 7. Booking a pool/game-zone slot

1. Open **Resource Booking** > New.
2. Pick the **Resource** (e.g. Main Pool), the **Room Booking** it belongs
   to, the date, and the start/end time.
3. Save. If the slot falls outside the resource's operating hours, or the
   resource is already full for that time, you'll be told immediately and
   asked to pick another time.

---

## 8. Who can do what

- **Receptionist**: create/manage bookings, guests, payments (Advance/
  Balance) and resource bookings; view rooms, rates and reports. Cannot
  cancel a booking, record a refund, or edit rates/masters.
- **Resort Manager**: everything a Receptionist can do, plus cancellations,
  refunds, editing rooms/rates/masters, and Resort Settings.
