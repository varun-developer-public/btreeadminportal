document.addEventListener('DOMContentLoaded', function() {
    const modulesContainer = document.getElementById('modules-container');
    const totalDurationInput = document.getElementById('id_total_duration');
    const validationMessageDiv = document.getElementById('duration-validation-message');
    const addModuleBtn = document.getElementById('add-module-btn');
    const saveButton = document.querySelector('button[type="submit"]');

    function updateFormPrefixes() {
        const moduleForms = modulesContainer.querySelectorAll('.module-form');
        const totalModuleFormsInput = document.querySelector('input[name="modules-TOTAL_FORMS"]');
        if (totalModuleFormsInput) {
            totalModuleFormsInput.value = moduleForms.length;
        }

        moduleForms.forEach((moduleForm, moduleIndex) => {
            const modulePrefix = `modules-${moduleIndex}`;
            moduleForm.id = modulePrefix;
            moduleForm.querySelectorAll('[name^="modules-"]').forEach(input => {
                const name = input.name.replace(/modules-\d+-/, `${modulePrefix}-`);
                input.name = name;
                input.id = `id_${name}`;
            });

            const topicFormsContainer = moduleForm.querySelector('.topic-forms-container');
            if (topicFormsContainer) {
                const topicForms = topicFormsContainer.querySelectorAll('.topic-form');
                const totalTopicFormsInput = moduleForm.querySelector(`input[name^="topics-${modulePrefix}-TOTAL_FORMS"]`);
                if (totalTopicFormsInput) {
                    totalTopicFormsInput.value = topicForms.length;
                }

                topicForms.forEach((topicForm, topicIndex) => {
                    const topicPrefix = `topics-${modulePrefix}-${topicIndex}`;
                    topicForm.id = topicPrefix;
                    topicForm.querySelectorAll('[name^="topics-"]').forEach(input => {
                        const name = input.name.replace(/topics-modules-\d+-\d+-/, `${topicPrefix}-`);
                        input.name = name;
                        input.id = `id_${name}`;
                    });
                });
            }
        });
    }

    function validateDurations() {
        let totalModulesDuration = 0;
        modulesContainer.querySelectorAll('.module-form').forEach(moduleForm => {
            if (moduleForm.querySelector('input[name$="-DELETE"]')?.checked) return;

            const hasTopics = moduleForm.querySelector('input[name$="-has_topics"]')?.checked;
            const moduleHoursInput = moduleForm.querySelector('input[name$="-module_duration"]');
            let moduleDuration = 0;

            if (hasTopics) {
                let totalTopicsDuration = 0;
                moduleForm.querySelectorAll('.topic-form').forEach(topicForm => {
                    if (topicForm.querySelector('input[name$="-DELETE"]')?.checked) return;
                    const topicHoursInput = topicForm.querySelector('input[name$="-topic_duration"]');
                    totalTopicsDuration += parseInt(topicHoursInput?.value) || 0;
                });
                moduleDuration = totalTopicsDuration;
                if (moduleHoursInput) {
                    moduleHoursInput.value = moduleDuration;
                    moduleHoursInput.readOnly = true;
                }
            } else {
                if (moduleHoursInput) {
                    moduleHoursInput.readOnly = false;
                    moduleDuration = parseInt(moduleHoursInput.value) || 0;
                }
            }
            totalModulesDuration += moduleDuration;
        });

        const courseTotalDuration = parseInt(totalDurationInput.value) || 0;
        if (totalModulesDuration !== courseTotalDuration) {
            validationMessageDiv.textContent = `The sum of module durations (${totalModulesDuration} hours) must equal the total course duration (${courseTotalDuration} hours).`;
            validationMessageDiv.className = 'error';
            saveButton.disabled = true;
        } else {
            validationMessageDiv.textContent = 'Module durations match the total course duration.';
            validationMessageDiv.className = 'success';
            saveButton.disabled = false;
        }
    }

    function addTopicToModule(moduleForm) {
        const modulePrefix = moduleForm.id;
        const topicFormsContainer = moduleForm.querySelector('.topic-forms-container');
        const topicFormCount = topicFormsContainer.querySelectorAll('.topic-form').length;
        const topicTemplate = document.getElementById('topic-template').innerHTML;
        const newTopicHtml = topicTemplate
            .replace(/__module_prefix__/g, modulePrefix.replace('modules-',''))
            .replace(/__prefix__/g, topicFormCount);
        
        topicFormsContainer.insertAdjacentHTML('beforeend', newTopicHtml);
        const newTopicForm = topicFormsContainer.lastElementChild;
        attachTopicEvents(newTopicForm);
        updateFormPrefixes();
    }

    function attachTopicEvents(topicForm) {
        topicForm.querySelector('input[name$="-DELETE"]').addEventListener('change', function() {
            topicForm.style.display = this.checked ? 'none' : 'block';
            validateDurations();
        });
        topicForm.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
            input.addEventListener('input', validateDurations);
        });
    }

    function attachModuleEvents(moduleForm) {
        moduleForm.querySelector('input[name$="-DELETE"]').addEventListener('change', function() {
            moduleForm.style.display = this.checked ? 'none' : 'block';
            validateDurations();
        });

        const hasTopicsCheckbox = moduleForm.querySelector('input[name$="-has_topics"]');
        if (hasTopicsCheckbox) {
            hasTopicsCheckbox.addEventListener('change', function() {
                const topicsSection = moduleForm.querySelector('.topics-section');
                topicsSection.classList.toggle('d-none', !this.checked);
                if (!this.checked) {
                    topicsSection.querySelector('.topic-forms-container').innerHTML = '';
                }
                validateDurations();
            });
        }

        const addTopicBtn = moduleForm.querySelector('.add-topic-btn');
        if (addTopicBtn) {
            addTopicBtn.addEventListener('click', () => addTopicToModule(moduleForm));
        }

        moduleForm.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
            input.addEventListener('input', validateDurations);
        });
    }

    addModuleBtn.addEventListener('click', function() {
        const moduleTemplate = document.getElementById('module-template').innerHTML;
        const totalForms = modulesContainer.querySelectorAll('.module-form').length;
        const newModuleHtml = moduleTemplate.replace(/__prefix__/g, totalForms);
        modulesContainer.insertAdjacentHTML('beforeend', newModuleHtml);
        const newModuleForm = modulesContainer.lastElementChild;
        attachModuleEvents(newModuleForm);
        updateFormPrefixes();
    });

    modulesContainer.querySelectorAll('.module-form').forEach(attachModuleEvents);
    modulesContainer.querySelectorAll('.topic-form').forEach(attachTopicEvents);

    totalDurationInput.addEventListener('input', validateDurations);
    validateDurations();
});