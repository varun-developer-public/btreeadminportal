document.addEventListener('DOMContentLoaded', function() {
    const modulesContainer = document.getElementById('modules-container');
    const totalDurationInput = document.getElementById('id_total_duration');
    const validationMessageDiv = document.getElementById('duration-validation-message');
    const addModuleBtn = document.getElementById('add-module-btn');
    const categorySelect = document.getElementById('id_category');
    const codeInput = document.getElementById('id_code');
    const saveButton = document.querySelector('button[type="submit"]');

    let formInteracted = false;

    function setFormInteracted() {
        if (!formInteracted) {
            formInteracted = true;
        }
        validateDurations();
    }

    function validateRequiredFields() {
        let allRequiredFilled = true;
        const moduleForms = modulesContainer.querySelectorAll('.module-form');

        moduleForms.forEach((moduleForm, index) => {
            const moduleNameInput = moduleForm.querySelector('input[name="module_name"]');
            const moduleHoursInput = moduleForm.querySelector('input[name="module_hours"]');
            
            if (!moduleNameInput.value) {
                allRequiredFilled = false;
                if (formInteracted) moduleNameInput.classList.add('is-invalid');
            } else {
                moduleNameInput.classList.remove('is-invalid');
            }

            if (!moduleHoursInput.value) {
                allRequiredFilled = false;
                if (formInteracted) moduleHoursInput.classList.add('is-invalid');
            } else {
                moduleHoursInput.classList.remove('is-invalid');
            }

            const hasTopics = moduleForm.querySelector('.has-topics-checkbox').checked;
            if (hasTopics) {
                const topicNameInputs = moduleForm.querySelectorAll(`input[name^="topic_name_module_${index}"]`);
                const topicHoursInputs = moduleForm.querySelectorAll(`input[name^="topic_hours_module_${index}"]`);

                topicNameInputs.forEach(input => {
                    if (!input.value) {
                        allRequiredFilled = false;
                        if (formInteracted) input.classList.add('is-invalid');
                    } else {
                        input.classList.remove('is-invalid');
                    }
                });

                topicHoursInputs.forEach(input => {
                    if (!input.value) {
                        allRequiredFilled = false;
                        if (formInteracted) input.classList.add('is-invalid');
                    } else {
                        input.classList.remove('is-invalid');
                    }
                });
            }
        });
        return allRequiredFilled;
    }

    function validateDurations() {
        let totalModulesDuration = 0;
        const moduleForms = modulesContainer.querySelectorAll('.module-form');

        moduleForms.forEach((moduleForm, index) => {
            const hasTopics = moduleForm.querySelector('.has-topics-checkbox').checked;
            const moduleHoursInput = moduleForm.querySelector('input[name="module_hours"]');

            if (hasTopics) {
                const topicInputs = moduleForm.querySelectorAll(`input[name^="topic_hours_module_${index}"]`);
                let totalTopicsDuration = 0;
                topicInputs.forEach(input => {
                    totalTopicsDuration += parseInt(input.value) || 0;
                });
                
                moduleHoursInput.value = totalTopicsDuration;
                moduleHoursInput.readOnly = true;
                totalModulesDuration += totalTopicsDuration;
            } else {
                moduleHoursInput.readOnly = false;
                totalModulesDuration += parseInt(moduleHoursInput.value) || 0;
            }
        });

        const courseTotalDuration = parseInt(totalDurationInput.value) || 0;
        const allRequiredFilled = validateRequiredFields();

        if (!formInteracted) {
            validationMessageDiv.style.display = 'none';
            saveButton.disabled = false; // Enable by default on update page
            return;
        }
        
        validationMessageDiv.style.display = 'block';

        if (totalModulesDuration !== courseTotalDuration || !allRequiredFilled) {
            let errorMessages = [];
            if (totalModulesDuration !== courseTotalDuration) {
                errorMessages.push(`The sum of module durations (${totalModulesDuration} hours) must equal the total course duration (${courseTotalDuration} hours).`);
            }
            if (!allRequiredFilled) {
                errorMessages.push('Please fill in all required fields.');
            }
            validationMessageDiv.textContent = errorMessages.join(' ');
            validationMessageDiv.className = 'error';
            saveButton.disabled = true;
        } else {
            validationMessageDiv.textContent = 'Module durations match the total course duration.';
            validationMessageDiv.className = 'success';
            saveButton.disabled = false;
        }
    }

    function addTopicToModule(moduleDiv) {
        const moduleIndex = Array.from(modulesContainer.children).indexOf(moduleDiv);
        const tmpl = document.getElementById('topic-template').content.cloneNode(true);
        const topicDiv = tmpl.querySelector('.topic-form');
        
        const topicNameInput = topicDiv.querySelector('input[name="topic_name"]');
        topicNameInput.name = `topic_name_module_${moduleIndex}`;
        
        const topicHoursInput = topicDiv.querySelector('input[name="topic_hours"]');
        topicHoursInput.name = `topic_hours_module_${moduleIndex}`;

        topicDiv.querySelector('.remove-topic-btn').onclick = function() {
            topicDiv.remove();
            validateDurations();
        };
        moduleDiv.querySelector('.topic-forms-container').appendChild(topicDiv);
        
        const topicInputs = topicDiv.querySelectorAll('input');
        topicInputs.forEach(input => {
            input.addEventListener('input', setFormInteracted);
            input.addEventListener('blur', setFormInteracted);
        });
    }

    function attachModuleEvents(moduleDiv) {
        moduleDiv.querySelector('.remove-module-btn').onclick = function() {
            moduleDiv.remove();
            validateDurations();
        };

        const hasTopics = moduleDiv.querySelector('.has-topics-checkbox');
        const topicsSection = moduleDiv.querySelector('.topics-section');
        const addTopicBtn = moduleDiv.querySelector('.add-topic-btn');
        const topicFormsContainer = moduleDiv.querySelector('.topic-forms-container');

        hasTopics.onchange = function() {
            const moduleIndex = Array.from(modulesContainer.children).indexOf(moduleDiv);
            hasTopics.name = `has_topics_module_${moduleIndex}`;
            if (hasTopics.checked) {
                topicsSection.style.display = 'block';
                if (!topicFormsContainer.querySelector('.topic-form')) {
                    addTopicToModule(moduleDiv);
                }
            } else {
                topicsSection.style.display = 'none';
                topicFormsContainer.innerHTML = '';
            }
            setFormInteracted();
        };

        addTopicBtn.onclick = function() {
            addTopicToModule(moduleDiv);
        };

        const inputs = moduleDiv.querySelectorAll('input[name="module_name"], input[name="module_hours"], .has-topics-checkbox');
        inputs.forEach(input => {
            input.addEventListener('input', setFormInteracted);
            input.addEventListener('blur', setFormInteracted);
        });

        const topicInputs = moduleDiv.querySelectorAll('.topic-form input');
        topicInputs.forEach(input => {
            input.addEventListener('input', setFormInteracted);
            input.addEventListener('blur', setFormInteracted);
        });

        const removeTopicBtns = moduleDiv.querySelectorAll('.remove-topic-btn');
        removeTopicBtns.forEach(btn => {
            btn.onclick = function() {
                btn.closest('.topic-form').remove();
                validateDurations();
            };
        });
    }

    function addModule() {
        const tmpl = document.getElementById('module-template').content.cloneNode(true);
        const moduleDiv = tmpl.querySelector('.module-form');
        attachModuleEvents(moduleDiv);
        modulesContainer.appendChild(moduleDiv);
        validateDurations();
    }

    if (addModuleBtn) {
        addModuleBtn.onclick = addModule;
    }

    // Attach events to existing modules on update page
    const existingModules = modulesContainer.querySelectorAll('.module-form');
    existingModules.forEach(moduleDiv => {
        attachModuleEvents(moduleDiv);
    });

    if (categorySelect && codeInput) {
        categorySelect.addEventListener('change', function() {
            const categoryId = this.value;
            if (categoryId) {
                fetch(`/coursedb/ajax/get_next_course_code/?category_id=${categoryId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.next_code) {
                            codeInput.value = data.next_code;
                        }
                    })
                    .catch(error => console.error('Error fetching next course code:', error));
            }
        });
    }

    totalDurationInput.addEventListener('input', setFormInteracted);
    totalDurationInput.addEventListener('blur', setFormInteracted);

    validateDurations();
});