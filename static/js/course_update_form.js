document.addEventListener('DOMContentLoaded', function() {
    const modulesContainer = document.getElementById('modules-container');
    const addModuleBtn = document.getElementById('add-module-btn');
    const totalDurationInput = document.getElementById('id_total_duration');
    const validationMessageDiv = document.getElementById('duration-validation-message');
    const courseForm = document.getElementById('course-form');
    const realtimeCalculationSpan = document.getElementById('realtime-calculation');
    const categorySelect = document.getElementById('id_category');
    const courseCodeInput = document.getElementById('id_code');

    let moduleIndex = modulesContainer.querySelectorAll('.module-form').length;

    function updateTotalDuration() {
        let totalHours = 0;
        modulesContainer.querySelectorAll('.module-form').forEach(moduleForm => {
            const hasTopics = moduleForm.querySelector('.has-topics-checkbox').checked;
            if (hasTopics) {
                let topicHours = 0;
                moduleForm.querySelectorAll('.topic-hours-input').forEach(input => {
                    topicHours += Number(input.value) || 0;
                });
                moduleForm.querySelector('.module-hours-input').value = topicHours;
                totalHours += topicHours;
            } else {
                totalHours += Number(moduleForm.querySelector('.module-hours-input').value) || 0;
            }
        });
        
        realtimeCalculationSpan.innerHTML = `Calculated Total: <strong>${totalHours}</strong> hours`;

        const courseTotalDuration = Number(totalDurationInput.value) || 0;
        const saveButton = courseForm.querySelector('button[type="submit"]');
        if (totalHours !== courseTotalDuration) {
            validationMessageDiv.innerHTML = `<strong>Validation Error:</strong> module durations (<strong>${totalHours}</strong> hours) must equal to course duration (<strong>${courseTotalDuration}</strong> hours).`;
            validationMessageDiv.className = 'alert alert-danger';
            saveButton.disabled = true;
        } else {
            validationMessageDiv.innerHTML = ``
            validationMessageDiv.className = '';
            saveButton.disabled = false;
        }
    }

    function addModule() {
        const newModule = `
            <div class="module-form" data-module-index="${moduleIndex}">
                <div class="row">
                    <div class="col-md-5">
                        <div class="form-group">
                            <label>Module Name<span class="required-indicator">*</span></label>
                            <input type="text" name="module_name" class="form-control" required>
                        </div>
                    </div>
                    <div class="col-md-5">
                        <div class="form-group">
                            <label>Module Hours<span class="required-indicator">*</span></label>
                            <input type="number" name="module_hours" class="form-control module-hours-input" min="0.5" step="0.01" required>
                        </div>
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <button type="button" class="btn btn-danger remove-module-btn">Remove</button>
                    </div>
                </div>
                <div class="form-group">
                    <label style="font-weight:normal;">
                        <input type="checkbox" name="has_topics_module_${moduleIndex}" class="has-topics-checkbox">
                        Has Topics?
                    </label>
                </div>
                <div class="topics-section d-none">
                    <h6>Topics</h6>
                    <div class="topic-forms-container"></div>
                    <button type="button" class="btn btn-sm btn-secondary add-topic-btn">Add Topic</button>
                </div>
            </div>
        `;
        modulesContainer.insertAdjacentHTML('beforeend', newModule);
        moduleIndex++;
    }

    function addTopic(moduleForm) {
        const currentModuleIndex = moduleForm.dataset.moduleIndex;
        let topicIndex = moduleForm.querySelectorAll('.topic-form').length;
        const newTopic = `
            <div class="topic-form" data-topic-index="${topicIndex}">
                <div class="row">
                    <div class="col-md-5">
                        <div class="form-group">
                            <label>Topic Name<span class="required-indicator">*</span></label>
                            <input type="text" name="topic_name_module_${currentModuleIndex}" class="form-control" required>
                        </div>
                    </div>
                    <div class="col-md-5">
                        <div class="form-group">
                            <label>Topic Hours<span class="required-indicator">*</span></label>
                            <input type="number" name="topic_hours_module_${currentModuleIndex}" class="form-control topic-hours-input" min="0.5" step="0.01" required>
                        </div>
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <button type="button" class="btn btn-danger remove-topic-btn">Remove</button>
                    </div>
                </div>
            </div>
        `;
        moduleForm.querySelector('.topic-forms-container').insertAdjacentHTML('beforeend', newTopic);
    }

    addModuleBtn.addEventListener('click', addModule);

    modulesContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-module-btn')) {
            e.target.closest('.module-form').remove();
            updateTotalDuration();
        }
        if (e.target.classList.contains('add-topic-btn')) {
            addTopic(e.target.closest('.module-form'));
        }
        if (e.target.classList.contains('remove-topic-btn')) {
            e.target.closest('.topic-form').remove();
            updateTotalDuration();
        }
    });

    modulesContainer.addEventListener('change', function(e) {
        if (e.target.classList.contains('has-topics-checkbox')) {
            const moduleForm = e.target.closest('.module-form');
            const topicsSection = moduleForm.querySelector('.topics-section');
            const moduleHoursInput = moduleForm.querySelector('.module-hours-input');
            if (e.target.checked) {
                topicsSection.classList.remove('d-none');
                moduleHoursInput.readOnly = true;
                addTopic(moduleForm);
            } else {
                topicsSection.classList.add('d-none');
                moduleHoursInput.readOnly = false;
                moduleForm.querySelector('.topic-forms-container').innerHTML = '';
            }
            updateTotalDuration();
        }
    });

    modulesContainer.addEventListener('input', function(e) {
        if (e.target.classList.contains('module-hours-input') || e.target.classList.contains('topic-hours-input')) {
            updateTotalDuration();
        }
    });

    function getNextCourseCode() {
        const categoryId = categorySelect.value;
        if (categoryId) {
            fetch(`/coursedb/ajax/get_next_course_code/?category_id=${categoryId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.next_code) {
                        courseCodeInput.value = data.next_code;
                    }
                });
        }
    }

    totalDurationInput.addEventListener('input', updateTotalDuration);
    categorySelect.addEventListener('change', getNextCourseCode);

    courseForm.addEventListener('submit', function(e) {
        let totalHours = 0;
        modulesContainer.querySelectorAll('.module-form').forEach(moduleForm => {
            const hasTopics = moduleForm.querySelector('.has-topics-checkbox').checked;
            if (hasTopics) {
                let topicHours = 0;
                moduleForm.querySelectorAll('.topic-hours-input').forEach(input => {
                    topicHours += Number(input.value) || 0;
                });
                totalHours += topicHours;
            } else {
                totalHours += Number(moduleForm.querySelector('.module-hours-input').value) || 0;
            }
        });

        const courseTotalDuration = Number(totalDurationInput.value) || 0;
        if (totalHours !== courseTotalDuration) {
            e.preventDefault();
            validationMessageDiv.textContent = 'Cannot submit: The sum of module durations must equal the total course duration.';
            validationMessageDiv.style.color = 'red';
        }
    });

    // Initial setup
    modulesContainer.querySelectorAll('.module-form').forEach(moduleForm => {
        const hasTopicsCheckbox = moduleForm.querySelector('.has-topics-checkbox');
        const topicsSection = moduleForm.querySelector('.topics-section');
        const moduleHoursInput = moduleForm.querySelector('.module-hours-input');
        if (hasTopicsCheckbox.checked) {
            topicsSection.classList.remove('d-none');
            moduleHoursInput.readOnly = true;
        } else {
            topicsSection.classList.add('d-none');
            moduleHoursInput.readOnly = false;
        }
    });

    updateTotalDuration();
});