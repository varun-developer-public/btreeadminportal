document.addEventListener('DOMContentLoaded', function() {
    const moduleFormsContainer = document.getElementById('module-forms-container');
    const addModuleBtn = document.getElementById('add-module-btn');
    const emptyModuleFormTemplate = document.getElementById('empty-form-template');
    const totalDurationInput = document.getElementById('id_total_duration');
    const saveButton = document.getElementById('save-button');
    const durationError = document.getElementById('duration-error');
    const categorySelect = document.getElementById('id_category');
    const codeInput = document.getElementById('id_code');

    if (!moduleFormsContainer) return;

    const updateTotal = () => {
        if (!totalDurationInput || !durationError || !saveButton) return;

        let courseTotal = parseInt(totalDurationInput.value, 10) || 0;
        let modulesTotal = 0;
        let errorMessages = [];

        document.querySelectorAll('.module-form').forEach(moduleForm => {
            if (moduleForm.style.display === 'none') return;

            const moduleDurationInput = moduleForm.querySelector('input[name$="-module_duration"]');
            const moduleDuration = parseInt(moduleDurationInput.value, 10) || 0;
            modulesTotal += moduleDuration;

            const hasTopicsCheckbox = moduleForm.querySelector('input[name$="-has_topics"]');
            if (hasTopicsCheckbox && hasTopicsCheckbox.checked) {
                let topicsTotal = 0;
                moduleForm.querySelectorAll('.topic-form').forEach(topicForm => {
                    if (topicForm.style.display === 'none') return;
                    const topicDurationInput = topicForm.querySelector('input[name$="-topic_duration"]');
                    topicsTotal += parseInt(topicDurationInput.value, 10) || 0;
                });

                if (moduleDuration !== topicsTotal) {
                    const moduleName = moduleForm.querySelector('input[name$="-name"]').value || 'A module';
                    errorMessages.push(`Topics in '${moduleName}' sum to ${topicsTotal}hrs, but module is ${moduleDuration}hrs.`);
                }
            }
        });

        if (courseTotal !== modulesTotal) {
            errorMessages.push(`Modules sum to ${modulesTotal}hrs, but course is ${courseTotal}hrs.`);
        }

        durationError.innerHTML = errorMessages.join('<br>');
        durationError.style.display = errorMessages.length > 0 ? 'block' : 'none';
        saveButton.disabled = errorMessages.length > 0;
    };

    const setupTopicForm = (topicForm) => {
        topicForm.querySelector('.remove-topic-btn').addEventListener('click', () => {
            const deleteInput = topicForm.querySelector('input[name$="-DELETE"]');
            if (deleteInput) deleteInput.checked = true;
            topicForm.style.display = 'none';
            updateTotal();
        });
        topicForm.querySelector('input[name$="-topic_duration"]').addEventListener('input', updateTotal);
    };

    const setupModuleForm = (moduleForm) => {
        const hasTopicsCheckbox = moduleForm.querySelector('input[name$="-has_topics"]');
        const topicsSection = moduleForm.querySelector('.topics-section');
        const addTopicBtn = moduleForm.querySelector('.add-topic-btn');

        hasTopicsCheckbox.addEventListener('change', () => {
            const isChecked = hasTopicsCheckbox.checked;
            topicsSection.style.display = isChecked ? 'block' : 'none';
            addTopicBtn.style.display = isChecked ? 'inline-block' : 'none';
            updateTotal();
        });

        addTopicBtn.addEventListener('click', () => {
            const topicFormsContainer = moduleForm.querySelector('.topic-forms-container');
            const template = document.getElementById('empty-form-template').querySelector('.empty-topic-form-template').innerHTML;
            const totalFormsInput = moduleForm.querySelector('input[name$="-topics-TOTAL_FORMS"]');
            const newIndex = parseInt(totalFormsInput.value);
            
            const newFormHtml = template.replace(/__prefix__/g, newIndex);
            topicFormsContainer.insertAdjacentHTML('beforeend', newFormHtml);
            totalFormsInput.value = newIndex + 1;

            setupTopicForm(topicFormsContainer.lastElementChild);
            updateTotal();
        });

        moduleForm.querySelector('.remove-module-btn').addEventListener('click', () => {
            const deleteInput = moduleForm.querySelector('input[name$="-DELETE"]');
            if (deleteInput) deleteInput.checked = true;
            moduleForm.style.display = 'none';
            updateTotal();
        });

        moduleForm.querySelectorAll('.topic-form').forEach(setupTopicForm);
        moduleForm.querySelector('input[name$="-module_duration"]').addEventListener('input', updateTotal);
    };

    addModuleBtn.addEventListener('click', () => {
        const totalFormsInput = document.querySelector('#id_modules-TOTAL_FORMS');
        const newIndex = parseInt(totalFormsInput.value);
        const newFormHtml = emptyModuleFormTemplate.innerHTML.replace(/__prefix__/g, newIndex);
        
        moduleFormsContainer.insertAdjacentHTML('beforeend', newFormHtml);
        totalFormsInput.value = newIndex + 1;

        setupModuleForm(moduleFormsContainer.lastElementChild);
        updateTotal();
    });

    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            const categoryId = categorySelect.value;
            if (categoryId) {
                const url = document.body.dataset.getCodeUrl;
                fetch(`${url}?category_id=${categoryId}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.next_code) codeInput.value = data.next_code;
                    });
            }
        });
    }

    document.querySelectorAll('.module-form').forEach(setupModuleForm);
    if (totalDurationInput) totalDurationInput.addEventListener('input', updateTotal);
    updateTotal();
});