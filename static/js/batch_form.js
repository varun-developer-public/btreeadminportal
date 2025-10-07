$(document).ready(function() {
    // Initialize Select2
    $('#id_course_category, #id_course, #id_trainer, #id_students, #id_time_slot').select2();

    const courseCategory = $('#id_course_category');
    const course = $('#id_course');
    const trainer = $('#id_trainer');
    const timeSlot = $('#id_time_slot');
    const students = $('#id_students');
    const startDateInput = $('#id_start_date');
    const endDateInput = $('#id_end_date');
    const hoursPerDayInput = $('#id_hours_per_day');
    const batchDaysCheckboxes = $('input[name="batch_days"]');

    function updateCourses() {
        const categoryId = courseCategory.val();
        course.empty().append('<option value="">Select a course</option>').prop('disabled', true);
        trainer.empty().append('<option value="">Select a trainer</option>').prop('disabled', true);
        timeSlot.empty().append('<option value="">Select a time slot</option>').prop('disabled', true);
        students.empty().prop('disabled', true);

        if (categoryId) {
            $.ajax({
                url: '/batches/ajax/get-courses-by-category/',
                data: { 'category_id': categoryId },
                success: function(data) {
                    course.prop('disabled', false);
                    data.forEach(c => course.append(`<option value="${c.id}">${c.course_name}</option>`));
                    if (typeof batchData !== 'undefined' && batchData.courseId) {
                        course.val(batchData.courseId).trigger('change');
                    }
                }
            });
        }
    }

    function updateTrainersAndStudents() {
        const courseId = course.val();
        trainer.empty().append('<option value="">Select a trainer</option>').prop('disabled', true);
        timeSlot.empty().append('<option value="">Select a time slot</option>').prop('disabled', true);
        students.empty().prop('disabled', true);

        if (courseId) {
            // Fetch Trainers
            $.ajax({
                url: '/batches/ajax/get-trainers-for-course/',
                data: { 'course_id': courseId },
                success: function(data) {
                    trainer.prop('disabled', false);
                    data.forEach(t => trainer.append(`<option value="${t.id}">${t.trainer_id}- ${t.name}</option>`));
                    if (typeof batchData !== 'undefined' && batchData.trainerId) {
                        trainer.val(batchData.trainerId).trigger('change');
                    }
                }
            });

            // Fetch Students
            $.ajax({
                url: '/batches/ajax/get-students-for-course/',
                data: { 'course_id': courseId, 'exclude_students_in_any_batch': true },
                success: function(data) {
                    students.prop('disabled', false);
                    data.forEach(s => students.append(`<option value="${s.id}">${s.student_id}- ${s.first_name} ${s.last_name || ''}</option>`));
                    if (typeof batchData !== 'undefined' && batchData.studentIds) {
                        students.val(batchData.studentIds).trigger('change');
                    }
                }
            });
        }
    }

    function updateTimeSlots() {
        const trainerId = trainer.val();
        timeSlot.empty().append('<option value="">Select a time slot</option>').prop('disabled', true);

        if (trainerId) {
            $.ajax({
                url: '/batches/ajax/get-trainer-slots/',
                data: { 'trainer_id': trainerId },
                success: function(data) {
                    timeSlot.prop('disabled', false);
                    data.forEach(slot => timeSlot.append(`<option value="${slot.id}">${slot.name}</option>`));
                    if (typeof batchData !== 'undefined' && batchData.timeSlot) {
                        timeSlot.val(batchData.timeSlot).trigger('change');
                    }
                }
            });
        }
    }

    function calculateEndDate() {
        const startDateStr = startDateInput.val();
        if (!startDateStr) return;

        const startDate = new Date(startDateStr);
        const hoursPerDay = parseInt(hoursPerDayInput.val());
        const selectedDaysCheckboxes = batchDaysCheckboxes.filter(':checked');
        const selectedDays = selectedDaysCheckboxes.map(function() { return parseInt($(this).val()); }).get();
        const courseId = course.val();

        if (startDate && hoursPerDay > 0 && selectedDays.length > 0 && courseId) {
            $.ajax({
                url: `/coursedb/ajax/course/${courseId}/get-duration/`,
                success: function(data) {
                    const totalHours = data.total_duration;
                    if (totalHours) {
                        let remainingHours = totalHours;
                        let currentDate = new Date(startDate);

                        while (remainingHours > 0) {
                            const dayOfWeek = currentDate.getDay(); // Sunday is 0, Monday is 1, etc.
                            if (selectedDays.includes(dayOfWeek)) {
                                remainingHours -= hoursPerDay;
                            }
                            if (remainingHours > 0) {
                                currentDate.setDate(currentDate.getDate() + 1);
                            }
                        }
                        endDateInput.val(currentDate.toISOString().split('T')[0]);
                    }
                }
            });
        }
    }

    courseCategory.on('change', updateCourses);
    course.on('change', updateTrainersAndStudents);
    trainer.on('change', updateTimeSlots);
    startDateInput.on('change', calculateEndDate);
    hoursPerDayInput.on('input', calculateEndDate);
    batchDaysCheckboxes.on('change', calculateEndDate);

    // Initial population for update form
    if (typeof batchData !== 'undefined') {
        if (batchData.batchDays) {
            batchData.batchDays.forEach(day => {
                $(`input[name="batch_days"][value="${day}"]`).prop('checked', true);
            });
        }
        courseCategory.trigger('change');
    }
});