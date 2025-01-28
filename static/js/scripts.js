document.addEventListener('DOMContentLoaded', function () {
  var collapseElements = document.querySelectorAll('.collapse');
  var sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  var mainSidebar = document.querySelector('.col-lg-3.side'); // Select the main sidebar
  var minimizedSidebar = document.querySelector('.col-lg-1.minimized-sidebar'); // Select the minimized sidebar

  collapseElements.forEach(function (collapseEl) {
    collapseEl.addEventListener('show.bs.collapse', function () {
      var collapseIcon = this.previousElementSibling.querySelector('.fas');
      if (collapseIcon) {
        collapseIcon.classList.remove('fa-plus-circle');
        collapseIcon.classList.add('fa-minus-circle');
      }
    });

    collapseEl.addEventListener('hide.bs.collapse', function () {
      var collapseIcon = this.previousElementSibling.querySelector('.fas');
      if (collapseIcon) {
        collapseIcon.classList.remove('fa-minus-circle');
        collapseIcon.classList.add('fa-plus-circle');
      }
    });
  });

  if (sidebarToggleBtn != null) {
    sidebarToggleBtn.addEventListener('click', function () {
      mainSidebar.classList.toggle('sidebar-hidden');
      minimizedSidebar.classList.toggle('minimized-sidebar-visible');

      // Toggle icon based on sidebar visibility
      var icon = this.querySelector('i');
      if (mainSidebar.classList.contains('sidebar-hidden')) {
        // Main sidebar is hidden, show "Caret right" icon
        icon.classList.remove('fa-caret-left');
        icon.classList.add('fa-caret-right');
      } else {
        // Main sidebar is visible, show "Caret left" icon
        icon.classList.remove('fa-caret-right');
        icon.classList.add('fa-caret-left');
      }

      // Adjust the body's class to make it full screen or not
      document.body.classList.toggle('body-fullscreen');
    });
  }
});

// Dynamically set Confirmation Dialog Title and Body
let confirmationDialog = document.getElementById('confirmationModal');
confirmationDialog.addEventListener('show.bs.modal', function (event) {
  let button = event.relatedTarget;
  let action = button.getAttribute('data-bs-action');
  let modalBodyClass = button.getAttribute('data-modal-body-class');
  let modalTitle = button.getAttribute('data-bs-title');
  let modalBody = button.getAttribute('data-bs-body');
  let modalTitleElement = confirmationDialog.querySelector('#confirmationModalLabel');
  let modalBodyElement = confirmationDialog.querySelector('#confirmationModalBody');
  modalBodyElement.className = 'modal-body';
  confirmationDialog.dataset.action = action;
  confirmationDialog.dataset.record_id = button.getAttribute('data-record-id');
  modalTitleElement.innerHTML = modalTitle;
  modalBodyElement.innerHTML = modalBody;
  modalBodyElement.classList.add(modalBodyClass);
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

let confirmationYesButton = document.getElementById('confirmationYesButton');
confirmationYesButton.addEventListener('click', function () {
  let confirmationDialog = document.getElementById('confirmationModal');
  let action = confirmationDialog.dataset.action;
  let record_id = confirmationDialog.dataset.record_id;
  let xhr = new XMLHttpRequest();
  if (action.split('_')[0] === 'customer') {
    if (action.split('_')[1] === 'delete') {
      xhr.open('POST', '/organogram/delete_customer/', true);
      openXhr(xhr, record_id);
    }
  } else if (action.split('_')[0] === 'memo') {
    if (action.split('_')[1] === 'approve') {
        acceptPIN('accept_pin',  'PIN Code', 'approve');
        disableEnablePinContinue();
        let pinCode = document.getElementById('id_pin_code');
        let confirmPinCode = document.getElementById('confirmPinCode');
        if (confirmPinCode) {
            confirmPinCode.addEventListener('click', function(event) {
                event.preventDefault();
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                fetch('/user/accept_pin/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({"pin": pinCode.value})
                }).then(response => response.json())
                    .then(data => {
                        if (data.message === 'success') {
                            xhr.open('POST', '/memotracker/approve_memo/', true);
                            openXhr(xhr, record_id);
                            $('#pinCodeModal').modal('hide');
                        } else {
                            $('#pinCodeModal').modal('hide');
                            // closePinCodeModal();

                            let message = 'The PIN Code you provided is incorrect try again!!!';
                            let toastBg = "bg-danger";
                            let toastHeader = 'Error';
                            displayToastMessage(message, toastBg, toastHeader);
                        }
                    });
            });
        }
    } else if (action.split('_')[1] === 'route') {
        if (action.split('_')[2] === 'delete') {
            let list_name = localStorage.getItem('listName');
            xhr.open('POST', '/memotracker/delete_memo_route/' + list_name, true);
            openXhr(xhr, record_id);
        } else if (action.split('_')[2] === 'public') {
            let createForm = document.getElementById("createMemoForm");
            createForm.action = '/memotracker/memo_route_to_all/';
            if (action.split('_')[3] === 'draft'){
                createForm.action = '/memotracker/memo_route_to_all/' + record_id + '/';
            }
            let memoDate = createForm['memo_date'].value;
            let dueDate = createForm['due_date'].value;
            if (!createForm['in_english'].checked) {
                memoDate = convertDateToGC(memoDate);
                if(dueDate !== "") {
                    dueDate = convertDateToGC(dueDate);
                }
            }
            createForm['memo_date'].setAttribute('type', 'date');
            createForm['memo_date'].valueAsDate = new Date(memoDate);
            createForm['due_date'].setAttribute('type', 'date');
            if(dueDate !== "")
                createForm['due_date'].valueAsDate = new Date(dueDate);
            createForm.submit();
        } else if (action.split('_')[2] === 'reverse'){
            let list_name = localStorage.getItem('listName');
            xhr.open('POST', '/memotracker/reverse_memo_route/' + list_name, true);
            openXhr(xhr, record_id);
        }
    } else if (action.split('_')[1] === 'approval') {
        if (action.split('_')[2] === 'delete') {
            xhr.open('POST', '/memotracker/delete_memo_approval/', true);
            openXhr(xhr, record_id);
        }
    }
  } else if (action.split('_')[0] === 'attachment') {
    if (action.split('_')[1] === 'delete') {
      xhr.open('POST', '/memotracker/memo_attachment_delete/', true);
      openXhr(xhr, record_id);
    }
  } else if (action.split('_')[0] === 'delete') {
    console.log('is delete=', action.split('_')[0])
    if (action.split('_')[1] === 'memo') {
      xhr.open('POST', '/memotracker/delete_memo/', true);
      openXhr(xhr, record_id);
    }
  }

//  else if (action.split('_')[0] === 'document') {
//    console.log('is delete=', action.split('_')[0])
//    if (action.split('_')[1] === 'delete') {
//      xhr.open('POST', `/dms/document/${record_id}/delete/`, true);
//      openXhr(xhr, record_id);
//    }
//  }
///////////////////////////////////////
  else if (action.split('_')[0] === 'document') {
    console.log('is delete=', action.split('_')[0]);
    if (action.split('_')[1] === 'delete') {
        // Confirmation dialog
       xhr.open('POST', `/dms/document/${record_id}/delete/`, true);
            openXhr(xhr, record_id);
            confirmationModal.style.display = 'none'; // Close the modal
            // Add an event listener to the XMLHttpRequest
            xhr.onload = function() {
                if (xhr.status === 200) {  // Change to 200 for successful deletion
                    // Show alert on successful deletion

                    alert("Document is deleted successfully!");
                    // Optionally, redirect or update the UI here
                } else {
                    // Handle error
                    alert("Error deleting document.");
                }
            };

            xhr.onerror = function() {
                alert("Network error. Please try again.");
            };
    }
}
///////////////////////////////////////
});

function openXhr(xhr, record_id) {
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const contentType = xhr.getResponseHeader('Content-Type');
                if (contentType && contentType.includes('application/json')) {
                    try {
                        let response = JSON.parse(xhr.response);
                        let message = response.message;
                        let toastBg = response.status == "success" ? "bg-success" : "bg-warning";
                        let toastHeader = response.status == "success" ? "Success" : "Warning";
                        displayToastMessage(message, toastBg, toastHeader);
                    } catch (error) {
                        console.error('Error parsing JSON:', error);
                    }
                } else {
                    console.log('Action performed successfully');
                    window.location.href = xhr.responseURL;
                }
                closeModal();
            } else {
                console.error('Error performing action');
            }
        }
    };
    xhr.send('id=' + record_id);
}

function closeModal() {
      // var bootstrapModal = new bootstrap.Modal(modalElement);
      let modalElement = document.getElementById('confirmationModal');
      let backdropElement = document.getElementsByClassName('modal-backdrop')[0];
      modalElement.style.display = 'none';
      modalElement.classList.remove('show');
      modalElement.setAttribute('aria-hidden', 'true');
      modalElement.removeAttribute('aria-modal');
      modalElement.removeAttribute('role');
      modalElement.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      document.body.removeAttribute('style');
      modalElement.removeAttribute('data-bs-backdrop');
      modalElement.setAttribute('data-bs-backdrop', 'true');
      backdropElement.remove();
}

let approvalCommentTextarea = document.getElementById('approval_comment');
let commentCounter = document.getElementById('comment_character_counter');

if (approvalCommentTextarea != null) {
  let maxLength = approvalCommentTextarea.getAttribute('maxlength');
  approvalCommentTextarea.title = 'Maximum ' + maxLength + ' characters';

  approvalCommentTextarea.addEventListener('input', function () {
    let currentLength = approvalCommentTextarea.value.length;
    let remainingLength = maxLength - currentLength;
    commentCounter.textContent = 'Characters remaining: ' + remainingLength;
  });
}


function uploadDocument(url, form_id, title) {
// Fetch the content of the "add_document" page

fetch(url)
.then(response => response.text())
.then(content => {
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = content;
   
    // Find the form element by its ID within the container
    const formElement = tempContainer.querySelector(`#${form_id}`);

    const myModal = new bootstrap.Modal(document.getElementById('modalContainer'));

    // Check if the form element exists
    if (formElement) {

      // Set the modal title
      const modalTitle = document.getElementById('ModalLabel');
      modalTitle.innerHTML = title;
      // Clear the modal body
      const modalBody = document.getElementById('modal_body');
      modalBody.innerHTML = '';

      // Append the form element to the modal body
      modalBody.appendChild(formElement);

      // Open the modal
      myModal.show();
    }

   // Add event listener to the form submission
   document.querySelector(`#${form_id}`).addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent default form submission

    // Get the form data
    var formData = new FormData(this);
    
    // Send the form data to the server using AJAX
    fetch(url, {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data =>{
      // Handle the response from the server
      // You can display a success message or perform any other necessary actions
      if(data.message==='success'){
        alert('Document saved successfully!');
        myModal.hide(); // Hide the modal after successful submission  
       // Store data.saved_document in localStorage before reloading the page
       localStorage.setItem('savedDocument', data.saved_document);

       window.location.reload();
      }else{
        alert('Error saving document!');}
    })
    .catch(error => {
      // Handle any errors that occur during the AJAX request
      console.error('Error saving document:-', error);
    });
  });
});
}
    const setMemoDate = (date) => {
        let lang = document.getElementById('id_in_english').checked;
        const memoDate =  document.getElementById('id_memo_date');
        document.getElementById('id_due_date').attributes['type'].value='date';
        $('#id_memo_date').calendarsPicker('destroy');
        if (lang) {
            memoDate.setAttribute('type', 'date');
            memoDate.valueAsDate = new Date();
            memoDate.value = date;
        } else {
            memoDate.setAttribute('type', 'text');
            memoDate.value = date;
        }
        
        // memoDate.readOnly=false;
    }

    const setMemoDateForEdit = (date) => {
            let lang = document.getElementById('id_in_english').checked;
            const memoDate =  document.getElementById('id_memo_date');
            let memoDateIcon = document.getElementById('memo_date_icon');
            $('#id_memo_date').calendarsPicker('destroy');
            if (lang) {
                memoDate.setAttribute('type', 'date');
                memoDate.classList.remove("is-calendarsPicker");
                memoDate.removeAttribute('style');
                memoDate.valueAsDate = new Date();
                memoDate.value = date;
            } else {
                memoDate.setAttribute('type', 'text');
                memoDate.value = date;
                memoDate.style.pointerEvents = "none";
                if (memoDateIcon) {
                    let dateField = $('#id_memo_date');

                    dateField.calendarsPicker({
                        calendar: $.calendars.instance('ethiopian', 'am'),
                        dateFormat: "dd/mm/yyyy",
                    });
                    memoDateIcon.addEventListener('click', function (event) {
                        event.preventDefault();
                        dateField.calendarsPicker('show');
                    });
                }

            }
    }

    const setDueDateForEdit = (date) => {
            let lang = document.getElementById('id_in_english').checked;
            const memoDueDate =  document.getElementById('id_due_date');
            let memoDueDateIcon = document.getElementById('memo_dueDate_icon');
            $('#id_due_date').calendarsPicker('destroy');
            if (lang) {
                memoDueDate.setAttribute('type', 'date');
                memoDueDate.removeAttribute('placeholder');
                memoDueDate.classList.remove("is-calendarsPicker");
                memoDueDate.valueAsDate = new Date();
                memoDueDate.value = date;
            } else {
                memoDueDate.setAttribute('type', 'text');
                memoDueDate.setAttribute('placeholder', 'dd/mm/yyyy');
                memoDueDate.value = date;
                if (memoDueDateIcon) {
                    let dateField = $('#id_due_date');

                    dateField.calendarsPicker({
                        calendar: $.calendars.instance('ethiopian', 'am'),
                        dateFormat: "dd/mm/yyyy",
                        onSelect: function() {
                            handleDueDateChange();
                        }
                    });
                    memoDueDateIcon.addEventListener('click', function (event) {
                        event.preventDefault();
                        dateField.calendarsPicker('show');
                    });
                }

            }
    }

    function handleDueDateChange() {
        const toastLiveExample = document.getElementById('liveToast');
        const toast_body = document.getElementById('id_tost_body');
        const toast_header = document.getElementById('id_tost_header');
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastLiveExample);
        const submitBtn = document.getElementById('sendInternalMemo');
        const saveDraftBtn = document.getElementById('id_save_draft');
        const approvalRouteAdd = document.getElementById('approvalRouteAdd');
        const sendToPublic = document.getElementById('sendToPublic');
        const sendDraftToPublic = document.getElementById('sendDraftToPublic');
        const updateMemoBtn = document.getElementById('updateMemoBtn');
        const draftApprovalRouteAdd = document.getElementById('draftApprovalRouteAdd');
        const sendDraftInternalMemo = document.getElementById('sendDraftInternalMemo');
        const dueDate = document.getElementById('id_due_date');
        const today = new Date().setHours(0, 0, 0, 0);
        let date = dueDate.value;
        if (date.split('/').length > 1)
            date = convertDateToGC(dueDate.value);
        const selectedDate = new Date(date).setHours(0, 0, 0, 0);
        if (selectedDate < today) {
            toast_body.textContent = 'Due date cannot be in the past. Please select a future date or today.';
            toast_header.textContent = 'Error';
            toastBootstrap.show();
            if (submitBtn)
                submitBtn.disabled = true;
            if (approvalRouteAdd)
                approvalRouteAdd.disabled = true;
            if (sendToPublic)
                sendToPublic.disabled = true;
            if (saveDraftBtn)
                saveDraftBtn.disabled = true;
            if (updateMemoBtn)
                updateMemoBtn.disabled = true;
            if (sendDraftInternalMemo)
                sendDraftInternalMemo.classList.add('disabledAnchor');
            if (draftApprovalRouteAdd)
                draftApprovalRouteAdd.classList.add('disabledAnchor');
            if (sendDraftToPublic)
                sendDraftToPublic.disabled = true;
        } else {
            let createMemoForm = document.getElementById('createMemoForm');
            let contentEditor = document.querySelector('#memoContent');
            let editor = CKEDITOR.instances[contentEditor.id];
            let isFormValid = createMemoForm.checkValidity() && editor.getData() !== "";
            if (isFormValid) {
                if (submitBtn)
                    submitBtn.disabled = false;
                if (approvalRouteAdd)
                    approvalRouteAdd.disabled = false;
                if (sendToPublic)
                    sendToPublic.disabled = false;
                if (saveDraftBtn)
                    saveDraftBtn.disabled = false;
                if (updateMemoBtn)
                    updateMemoBtn.disabled = false;
                if (sendDraftInternalMemo)
                    sendDraftInternalMemo.classList.remove('disabledAnchor');
                if (draftApprovalRouteAdd)
                    draftApprovalRouteAdd.classList.remove('disabledAnchor');
                if (sendDraftToPublic)
                    sendDraftToPublic.disabled = false;
            } else {
                if (submitBtn)
                    submitBtn.disabled = true;
                if (approvalRouteAdd)
                    approvalRouteAdd.disabled = true;
                if (sendToPublic)
                    sendToPublic.disabled = true;
                if (saveDraftBtn)
                    saveDraftBtn.disabled = true;
                if (updateMemoBtn)
                    updateMemoBtn.disabled = true;
                if (sendDraftInternalMemo)
                    sendDraftInternalMemo.classList.add('disabledAnchor');
                if (draftApprovalRouteAdd)
                    draftApprovalRouteAdd.classList.add('disabledAnchor');
                if (sendDraftToPublic)
                    sendDraftToPublic.disabled = true;
            }
        }
    }
    function handleFormChange() {
        let createMemoForm = document.getElementById('createMemoForm');
        let sendInternalMemo = document.getElementById('sendInternalMemo');
        const saveDraftBtn = document.getElementById('id_save_draft');
        let approvalRouteAdd = document.getElementById('approvalRouteAdd');
        const updateMemoBtn = document.getElementById('updateMemoBtn');
        const draftApprovalRouteAdd = document.getElementById('draftApprovalRouteAdd');
        const sendDraftInternalMemo = document.getElementById('sendDraftInternalMemo');
        const sendToPublic = document.getElementById('sendToPublic');
        const sendDraftToPublic = document.getElementById('sendDraftToPublic');
        const dueDate = document.getElementById('id_due_date');

        let contentEditor = document.querySelector('#memoContent');
        let editor = CKEDITOR.instances[contentEditor.id];
        let isFormValid = createMemoForm.checkValidity() && editor.getData() !== "";
        if (dueDate.value !== '') {
            handleDueDateChange();
        } else {
            if (sendInternalMemo) {
                sendInternalMemo.disabled = !isFormValid;
            }
            if (approvalRouteAdd) {
                approvalRouteAdd.disabled = !isFormValid;
            }
            if (updateMemoBtn) {
                updateMemoBtn.disabled = !isFormValid;
            }
            if (sendDraftInternalMemo) {
                if (isFormValid) {
                    sendDraftInternalMemo.classList.remove('disabledAnchor');
                } else {
                    sendDraftInternalMemo.classList.add('disabledAnchor');
                }
            }
            if (draftApprovalRouteAdd) {
                if (isFormValid) {
                    draftApprovalRouteAdd.classList.remove('disabledAnchor');
                } else {
                    draftApprovalRouteAdd.classList.add('disabledAnchor');
                }
            }
            if (sendToPublic) {
                sendToPublic.disabled = !isFormValid;
            }
            if (saveDraftBtn) {
                saveDraftBtn.disabled = !isFormValid;
            }
            if (sendDraftToPublic)
                sendDraftToPublic.disabled = !isFormValid;
        }
    }

    function convertDateToEC(date) {
        let letter_dateGC = date;
        let jdGC = $.calendars.instance('gregorian').newDate(
                    parseInt(letter_dateGC.substr(0,4), 10),
                    parseInt(letter_dateGC.substr(5,2), 10),
                    parseInt(letter_dateGC.substr(8,2), 10)).toJD();

        let dateEC = $.calendars.instance('ethiopian').fromJD(jdGC);

        let day = dateEC["_day"] < 10 ? "0" + dateEC["_day"] : dateEC["_day"];
        let month = dateEC["_month"] < 10 ? "0" + dateEC["_month"] : dateEC["_month"];

        return day + "/" + month + "/" + dateEC["_year"];
    }

    function convertDateToGC(date) {
        let letter_dateEC = date;
        let jdEC = $.calendars.instance('ethiopian').newDate(
                    parseInt(letter_dateEC.substr(6,4), 10),
                    parseInt(letter_dateEC.substr(3,2), 10),
                    parseInt(letter_dateEC.substr(0,2), 10)).toJD();

        let dateGC = $.calendars.instance('gregorian').fromJD(jdEC);

        let day = dateGC["_day"] < 10 ? "0" + dateGC["_day"] : dateGC["_day"];
        let month = dateGC["_month"] < 10 ? "0" + dateGC["_month"] : dateGC["_month"];

        return dateGC["_year"] + "-" + month + "-" + day;
}

      // This function sets the default owner type to be business unit and
      // Hide the external owner type from the select option
    const setMemoOwnerType = ()=>{
        const ownerType = document.getElementById('id_content_type');

        // Hide the external owner type option
        for (let i = 0; i < ownerType.options.length; i++) {
            
            // Compare the text content
                if (ownerType.options[i].text === 'External') {
                    // Select the option
                    ownerType.options[i].style.display = 'none';
                    break;
                }
        }

         // Set the default owner type to be business unit
         for (let i=0; i<ownerType.options.length; i++){
            if (ownerType.options[i].text == 'Business Unit'){
                ownerType.options[i].selected = true;
                break;
            }
        }
    }

    const hideExternalOwnerType = ()=>{
     // Hide the external owner type option
     const ownerType = document.getElementById('id_content_type');

     for (let i = 0; i < ownerType.options.length; i++) {
            
        // Compare the text content
            if (ownerType.options[i].text === 'External') {
                // Select the option
                ownerType.options[i].style.display = 'none';
                break;
            }
        }
    }

    function toggleElement() {
        const selectedElement = document.getElementById("id_content_type");
        const selectedValue = selectedElement.options[selectedElement.selectedIndex].text;
        const targetElement = document.getElementById("followUp");
        const targetElement1 = document.getElementById("id_public"); // Checkbox
        const labelElement = document.querySelector('label[for="id_public"]'); // Associated label

        if (selectedValue === "Personal") {
            targetElement.style.display = "none"; // Hide followUp
            targetElement1.style.display = "none"; // Hide checkbox
            if (labelElement) {
                labelElement.style.display = "none"; // Hide label
            }
        } else {
            targetElement.style.display = "block"; // Show followUp for other options
            targetElement1.style.display = "block"; // Show checkbox for other options
            if (labelElement) {
                labelElement.style.display = "block"; // Show label for other options
            }
        }
    }


    const generateReferenceNumber = (ethDate, selected_text, lastPersonalReferenceNumber, lastReferenceNumber) => {
        let year = new Date().getFullYear();
        let newReferenceNumber='';
        let parts = [];
        // check if memo is in_english
        const isEnglish = document.getElementById('id_in_english').checked;
        if(isEnglish){
            
            //reset reference number if new year
            if(selected_text == 'Business Unit'){
                parts = lastReferenceNumber.split('/');
                if(parseInt(parts[3]) != year){
                    newReferenceNumber = 'IPDC'+parts[1]+'/1/' + year.toString();
                }else{
                    let refNumber = parseInt(parts[2]) + 1;
                    newReferenceNumber = 'IPDC/' + parts[1] + '/' + refNumber.toString() + '/' + year.toString();
                }
            }else{
                parts = lastPersonalReferenceNumber.split('/');
                parts2 = lastPersonalReferenceNumber.split('/');
            
                if(parts.length>1){
                    if(parseInt(parts[2])==year){
                        let refNumber = parseInt(parts[1]) + 1;
                        newReferenceNumber = parts[0] + '/' + refNumber.toString() + '/' + year.toString();
                    }else{
                        newReferenceNumber = parts[0]+ '/1/' + year.toString();
                    }
                }else{
                    //if this is users first personal memo
                    newReferenceNumber = 'P' + user_id.toString() + '/1/' + year.toString();
                }
            }
            return newReferenceNumber;
        }else{
            //reset reference number if new year
            ethYear = ethDate.split('/')[2];
            if(selected_text == 'Business Unit'){
                parts = lastReferenceNumber.split('/');
                if(parseInt(parts[3]) != year){
                    newReferenceNumber = 'ኢፓልኮ/'+parts[1]+'/1/' + ethYear;
                }else{
                    let refNumber = parseInt(parts[2]) + 1;
                    newReferenceNumber = 'ኢፓልኮ/' + parts[1] + '/' + refNumber.toString() + '/' + ethYear;
                }
            }else{
                parts = lastPersonalReferenceNumber.split('/');
                //parts2 = lastPersonalReferenceNumber.split('/');
            
                if(parts.length>1){
                   
                    if(parseInt(parts[2])==year){
                        let refNumber = parseInt(parts[1]) + 1;
                        newReferenceNumber = parts[0] + '/' + refNumber.toString() + '/' + ethYear;
                    }else{
                        newReferenceNumber = parts[0]+ '/1/' + ethYear;
                    }
                }else{
                    //if this is users first personal memo
                    newReferenceNumber = 'P' + user_id.toString() + '/1/' + ethYear;
                }
            }
            return newReferenceNumber;
        }
    }

    const handleOwnerTypeChange = ()=>{
        let referenceNumber = document.getElementById('id_reference_number');
        const items = document.getElementById('id_content_type')

        //let isPersonal = false;
        let isManager = "{{ memo_type.role.is_manager }}" === "True";
        let isDelegate = "{{ memo_type.deligated }}" === "True";

        items.onchange = () => {
            selected_text = items.options[items.selectedIndex].text;
                console.log('selected text', selected_text)
            document.getElementById('id_reference_number').value = generateReferenceNumber(ethDate, selected_text, lastPersonalReferenceNumber, lastReferenceNumber);
            if (items.options[items.selectedIndex].text === 'Business Unit') {
                if (isManager || isDelegate) {
                    document.getElementById('sendInternalMemo').classList.add('btn-primary');
                    document.getElementById('sendInternalMemo').classList.remove('visually-hidden');
                    document.getElementById('approvalRouteAdd').classList.add('visually-hidden');
                    document.getElementById('approvalRouteAdd').classList.remove('btn-primary');
                } else {
                    document.getElementById('sendInternalMemo').classList.remove('btn-primary');
                    document.getElementById('sendInternalMemo').classList.add('visually-hidden');
                    document.getElementById('approvalRouteAdd').classList.remove('visually-hidden');
                    document.getElementById('approvalRouteAdd').classList.add('btn-primary');
                }
            } else {
                document.getElementById('sendInternalMemo').classList.add('btn-primary');
                document.getElementById('sendInternalMemo').classList.remove('visually-hidden');
                document.getElementById('approvalRouteAdd').classList.add('visually-hidden');
                document.getElementById('approvalRouteAdd').classList.remove('btn-primary');
            }
        }
    }

    // This function hides the external section when personal memo is selected
    const handlePersonalMemo = () =>{
        const memoType = document.getElementById('id_content_type').selectedOptions[0].text;
        const cont = document.querySelector('div#id_external_section').children;
        
        if (memoType === 'Personal') {
            for (let i = 0; i < cont.length; i++) {
                cont[i].style.display = 'none';
                let chkInput = cont[i].querySelector('input');
                if (chkInput)
                    chkInput.checked = false;
            }

            const langSection = document.querySelector('div#id_lang_section');
            langSection.style.paddingLeft = '90px';


        } else {
            for (let i = 0; i < cont.length; i++) {
                cont[i].style.display = 'block';
            }

            const langSection = document.querySelector('div#id_lang_section');
            langSection.style.paddingLeft = '0px';
           
        }
    }

    const resetMemoDate = (calledFrom)=>{
        // Get a reference to the form element
        const form = document.getElementById('createMemoForm');

        // Attach an event listener to the form's submit event
        form.addEventListener('submit', function(event) {
            // Prevent the default form submission
            event.preventDefault();

            // Get a reference to the form element you want to modify
            const actualMemoDate = document.getElementById('id_memo_date');
            const dueDateBox = document.getElementById('id_due_date');
            const lang = document.getElementById('id_in_english');
            let memoDate = actualMemoDate.value;
            let dueDate = dueDateBox.value;
            if (!lang.checked) {
                memoDate = convertDateToGC(actualMemoDate.value);
                if (dueDateBox.value !== '') {
                    dueDate = convertDateToGC(dueDateBox.value);
                }
            }
            actualMemoDate.setAttribute('type', 'date');
            actualMemoDate.valueAsDate = new Date(memoDate);
            dueDateBox.setAttribute('type', 'date');
            dueDateBox.valueAsDate = new Date(dueDate);
            console.log('actual date value', actualMemoDate)

            let inputElement = document.createElement("input");
            // Submit the form programmatically
            if(calledFrom === 'saveDraft') {
                inputElement.type = "hidden";
                inputElement.name = "save_draft";
                inputElement.value = "";
                form.appendChild(inputElement);
                form.submit();
            }
        });
    }

    let recipientLists = [];

function adjustElementList(itemList, itemCc) {
    let itemListParent = itemList.parentNode;
    let itemListGParent = itemListParent.parentNode;
    let itemListGgParent = itemListGParent.parentNode
    itemListGgParent.classList.remove("col-6");
    itemListGgParent.classList.add("col");
    itemList.classList.remove("col-10");
    itemList.classList.add("col");
    let itemCcParent = itemCc.parentNode;
    itemCcParent.classList.add("d-none");
}

function adjustSiblingDivHeight(recipientSelector, recipientListDiv) {
    const recipientSelectorHeight = recipientSelector.getBoundingClientRect().height;
    recipientListDiv.style.maxHeight = `${recipientSelectorHeight}px`;
}

function memoRoute(url, form_id, title, routingAction) {
    recipientLists = [];
    let createMemoForm;
    if (routingAction === 'Send Memo' || routingAction === 'Send Approval') {
    	resetMemoDate('sendMemo');
        createMemoForm = document.getElementById('createMemoForm');
    }
    if (routingAction === 'Send External Memo') {
        createMemoForm = document.getElementById('createExternalMemoForm');
    }

  fetch(url)
      .then(response => response.text())
      .then(content => {
        const temp1Container = document.createElement('div');
        temp1Container.innerHTML = content;
        const form1Element = temp1Container.querySelector(`#${form_id}`);
        const myRouteModal = new bootstrap.Modal(document.getElementById('routeModal'));

        if (form1Element.id === "routing") {
            const modal1Title = document.getElementById(('routeModalLabel'));
            modal1Title.innerHTML = title;
            const modal1Body = document.getElementById('routeModalBody');
            modal1Body.innerHTML = '';
            modal1Body.appendChild(form1Element);

            let formTypeInput = document.getElementById('formType');

            let recipientListDiv = document.getElementById('recipientListDiv');
            let recipientSelector = form1Element.querySelectorAll('fieldset')[0].querySelector('#recipientSelector');

            adjustSiblingDivHeight(recipientSelector, recipientListDiv);

            let recipientSelectorUL = recipientSelector.querySelector('ul');
            recipientSelectorUL.addEventListener('show.bs.tab', function(event) {
                const targetTabId = event.target.getAttribute('href');
                const activeTabContent = document.querySelector(targetTabId);
                setTimeout(function () {
                    const contentLoadedEvent = new CustomEvent('contentLoaded', {
                        bubbles: true,
                        cancelable: true,
                    });
                    activeTabContent.dispatchEvent(contentLoadedEvent);
                }, 500);

                activeTabContent.addEventListener('contentLoaded', function () {
                    adjustSiblingDivHeight(recipientSelector, recipientListDiv);
                });
            });

            let routingUListItems = document.createElement('ul');
            routingUListItems.setAttribute("id", "recipientLists");

            recipientListDiv.appendChild(routingUListItems);

            let buList = document.getElementById('buList');
            let buListFG = document.querySelector('#buList .form-group');
            let buListBox = null;

            let buList2 = document.getElementById('buList2');
            let buList2FG = document.querySelector('#buList2 .form-group');
            let buList2Box = buList2FG.querySelector('select');

            let userList = document.getElementById('userList');
            let userListFG = document.querySelector('#userList .form-group');
            let userListBox = userListFG.querySelector('select');

            let externalList = document.getElementById('externalList');
            let externalListFG = document.querySelector('#externalList .form-group');
            let externalListBox = externalListFG.querySelector('select');

            let toAllRecipient = document.getElementById('toAllRecipient');
            let toAllRecipientCheckBox = toAllRecipient.querySelector('input');

            let allCarbonCopy = document.getElementById('carbonCopy');
            let carbonCopyCheckBox = allCarbonCopy.querySelector('input');

            let addRecipientBtn = document.getElementById('addRecipientBtn');

            let externalTabLink = document.getElementById('externalTabLink');
            let businessUnitTabLink = document.getElementById('businessUnitTabLink');
            let userTabLink = document.getElementById('userTabLink');

            let externalTab = document.getElementById('externalTab');
            let businessUnitTab = document.getElementById('businessUnitTab');
            let userTab = document.getElementById('userTab');

            let isPersonalMemo = form1Element['content_type_routing'].value === "Personal";
            let isExternalMemo = form1Element['content_type_routing'].value === "External Customer";
            let isToExternal = form1Element['is_to_external'].value === "True";
            let content_type = form1Element['content_type_routing'].value;
            let currentUserBu = form1Element['current_user_bu'].value;
            if (routingAction === 'Send Memo' || routingAction === 'Send Approval') {
            	content_type = createMemoForm['content_type'].options[createMemoForm['content_type'].selectedIndex].text;
                isPersonalMemo = createMemoForm['content_type'].options[createMemoForm['content_type'].selectedIndex].text === "Personal";
                isToExternal = createMemoForm['to_external'].checked;
            }

            let formType = formTypeInput.value.split('-');

            if (formType[0] === 'Memo Route') {
                let isManager = document.getElementById('isManager').value.toLowerCase() === "true";
                let isDelegate = document.getElementById('isDelegate').value.toLowerCase() === "true";

                buList.classList.add("d-none");
                buList2.classList.add("d-none");
                externalList.classList.add("d-none");
                myRouteModal._dialog.classList.add("modal-lg");
                myRouteModal._dialog.classList.remove("modal");

                buListBox = buListFG.querySelector('select');

                getBusinessUnitUser(buList2Box, userListBox, parseInt(userListBox.value));

                if (isManager || isDelegate || isPersonalMemo || isExternalMemo || routingAction === 'Send External Memo') {
                    buList.classList.remove("d-none");
                    buList2.classList.remove("d-none");
                } else {
                    myRouteModal._dialog.classList.remove("modal-lg");
                    myRouteModal._dialog.classList.add("modal");
                    userListBox.removeAttribute("multiple");

                    recipientListDiv.classList.add("d-none");
                    addRecipientBtn.classList.add("d-none");

                    userTab.classList.add("show", "active");
                    userTabLink.classList.add("active");

                    businessUnitTabLink.classList.add("d-none");
                    businessUnitTabLink.classList.remove("active");
                    businessUnitTab.classList.remove("show");
                    businessUnitTab.classList.remove("active");

                    buListBox.removeAttribute("required");
                    buListBox.removeAttribute("multiple");
                    buListBox.value = null;

                    adjustElementList(userList, allCarbonCopy);
                }

                let memoStatus = document.getElementById("memoStatus");

                if ((memoStatus.value === "draft" || memoStatus.value === "approved") && routingAction !== 'Send External Memo') {
                    allCarbonCopy.classList.remove("d-none");
                }

                if (isToExternal && (memoStatus.value === "draft" || memoStatus.value === "approved")) {
                    externalList.classList.remove("d-none");
                } else {
                    externalList.classList.add("d-none");
                    externalTabLink.classList.remove("active");
                    externalTab.classList.remove("show");
                    externalTab.classList.remove("active");
                    let externalTabLinkParent = externalTabLink.parentNode;
                    externalTabLinkParent.classList.add("d-none");
                    businessUnitTabLink.classList.add("active");
                    businessUnitTab.classList.add("show", "active");
                }

                addRecipientBtn.addEventListener('click', function(event) {
                    event.preventDefault();
                    let isToExternal = (externalTab.classList.contains("show") && externalTab.classList.contains("active"));
                    let isToBusinessUnit = (businessUnitTab.classList.contains("show") && businessUnitTab.classList.contains("active"));
                    let isToUser = (userTab.classList.contains("show") && userTab.classList.contains("active"));
                    let recipientBox;
                    if (isToExternal) {
                        recipientBox = externalListBox;
                    } else if (isToBusinessUnit) {
                        recipientBox = buListBox;
                    } else if (isToUser) {
                        recipientBox = userListBox;
                    }
                    const selectedOptions = Array.from(recipientBox.selectedOptions).map(option => option.value);
                    let carbonCopy = carbonCopyCheckBox.checked;
                    let toAllRecipient = toAllRecipientCheckBox.checked;
                    addRecipient(recipientBox, selectedOptions, isToExternal, isToBusinessUnit, isToUser, carbonCopy, toAllRecipient, routingUListItems);
                    carbonCopyCheckBox.checked = false;
                    toAllRecipientCheckBox.checked = false;
                });

                if (content_type === "Business Unit") {
                    for (let i = 0; i < buListBox.options.length; i++) {
                        if (buListBox.options[i].value === currentUserBu) {
                            let currentBu = buListBox.options[i];
                            currentBu.classList.add("d-none");
                        }
                    }
                }

                if (formType[1] !== undefined) {
                  let carbonCopyIdentifier = document.getElementById("carbonCopyIdentifier");
                  if (!isExternalMemo) {
                    carbonCopyIdentifier.classList.remove("d-none");
                  }
                  myRouteModal._dialog.classList.add("modal");
                  myRouteModal._dialog.classList.remove("modal-lg");

                  recipientListDiv.classList.add("d-none");
                  addRecipientBtn.classList.add("d-none");
                  toAllRecipient.classList.add("d-none");

                  if (formType[1] === 'Edit to User') {
                      let userListLabel = userListFG.querySelector('label');
                      //userListLabel.classList.add("d-none");
                      buList.classList.add("d-none");
                      //buList2.classList.add("d-none");
                      externalList.classList.add("d-none");
                      buListBox.removeAttribute('required');
                      externalListBox.removeAttribute("multiple");
                      externalListBox.removeAttribute('required');
                      userListBox.removeAttribute("multiple");

                      externalTabLink.classList.remove("active");
                      externalTabLink.classList.add("disabled");
                      businessUnitTabLink.classList.remove("active");
                      businessUnitTabLink.classList.add("disabled");
                      userTabLink.classList.add("active");

                      externalTab.classList.remove("show", "active");
                      businessUnitTab.classList.remove("show", "active");
                      userTab.classList.add("show", "active");

                      adjustElementList(userList, allCarbonCopy);
                  } else if (formType[1] === 'Edit to Business Unit') {
                      userList.classList.add("d-none");
                      buList2.classList.add("d-none");
                      externalList.classList.add("d-none");
                      externalListBox.removeAttribute("multiple");
                      externalListBox.removeAttribute('required');
                      buListBox.removeAttribute("multiple");

                      externalTabLink.classList.remove("active");
                      externalTabLink.classList.add("disabled");
                      businessUnitTabLink.classList.add("active");
                      userTabLink.classList.remove("active");
                      userTabLink.classList.add("disabled");

                      externalTab.classList.remove("show", "active");
                      businessUnitTab.classList.add("show", "active");
                      userTab.classList.remove("show", "active");

                      adjustElementList(buList, allCarbonCopy);
                  } else if (formType[1] === 'Edit to External') {
                      userList.classList.add("d-none");
                      buList2.classList.add("d-none");
                      externalList.classList.remove("d-none");
                      externalListBox.removeAttribute("multiple");
                      buListBox.removeAttribute('required');
                      buListBox.removeAttribute('multiple');

                      let externalTabLi = externalTabLink.parentNode;
                      externalTabLi.classList.remove("d-none");
                      externalTabLink.classList.add("active");
                      externalTabLink.classList.remove("disabled");
                      businessUnitTabLink.classList.remove("active");
                      businessUnitTabLink.classList.add("disabled");
                      userTabLink.classList.remove("active");
                      userTabLink.classList.add("disabled");

                      externalTab.classList.add("show", "active");
                      businessUnitTab.classList.remove("show", "active");
                      userTab.classList.remove("show", "active");

                      adjustElementList(externalList, allCarbonCopy);
                  }
              }

              buList2Box.addEventListener('click', function (event) {
                  event.preventDefault();
                  getBusinessUnitUser(buList2Box, userListBox);
              });
            } else if (formType[0] === 'Approval Route') {
              recipientListDiv.classList.add("d-none");
              addRecipientBtn.classList.add("d-none");
              buListBox = buListFG.querySelector('input');
              buList.classList.add("d-none");
              buList2.classList.add("d-none");

              let externalTabLi = externalTabLink.parentNode;
              externalTabLi.classList.add("d-none");
              let businessUnitTabLi = businessUnitTabLink.parentNode;
              businessUnitTabLi.classList.add("d-none");

              externalTabLink.classList.remove("active");
              externalTabLink.classList.add("disabled");
              businessUnitTabLink.classList.remove("active");
              businessUnitTabLink.classList.add("disabled");
              userTabLink.classList.add("active");
              userTabLink.classList.add("d-none");

              externalTab.classList.remove("show", "active");
              businessUnitTab.classList.remove("show", "active");
              userTab.classList.add("show", "active");

              myRouteModal._dialog.classList.remove("modal-lg");
              myRouteModal._dialog.classList.add("modal");

              getBusinessUnitUser(buListBox, userListBox, parseInt(userListBox.value));

              adjustElementList(userList, allCarbonCopy);
          }

            let memoRouteCancel = document.getElementById("memoRouteCancel");
            memoRouteCancel.addEventListener("click", function(event) {
                event.stopPropagation();
                recipientLists = [];
                $('#routeModal').modal('hide');
            });

            myRouteModal.show();

            if (routingAction === 'Send Memo' || routingAction === 'Send Approval' || routingAction === 'Send External Memo') {
                sendMemo(form_id, myRouteModal, createMemoForm, routingAction, externalListBox, buListBox, userListBox);
            } else {
                routeSubmit(form_id, url, myRouteModal, routingAction, externalListBox, buListBox, userListBox);
            }
        } else {
            const modal1Title = document.getElementById(('routeModalLabel'));
            modal1Title.innerHTML = title;
            const modal1Body = document.getElementById('routeModalBody');
            modal1Body.innerHTML = '';
            modal1Body.appendChild(form1Element);
            myRouteModal._dialog.classList.remove("modal-lg");
            myRouteModal._dialog.classList.add("modal");

            let memoAction = document.querySelector('#memoAction .form-group');
            let memoRemark = document.querySelector('#memoRemark .form-group');
            let memoComment = document.querySelector('#memoComment .form-group');

            if (memoRemark) {
                let txtMemoRemark = memoRemark.querySelector('textarea');
                txtMemoRemark.setAttribute("disabled", "disabled");
            }
            if (memoComment) {
                let txtMemoComment = memoComment.querySelector('textarea');
                txtMemoComment.setAttribute("disabled", "disabled");
            }
            if (memoAction) {
                let memoActionSelect = memoAction.querySelector('select');
                memoActionSelect.setAttribute("disabled", "disabled");
            }

            let buList = document.getElementById('buList');
            let buListFG = document.querySelector('#buList .form-group');
            let buListBox = null;

            let userList = document.getElementById('userList');
            let userListFG = document.querySelector('#userList .form-group');
            let userListBox = userListFG.querySelector('select');

            let formTypeInput = document.getElementById('formType');
            let formType = formTypeInput.value.split('-');

            if (formType[0] === 'Memo Route') {
                if (formType[1] !== undefined) {
                  let carbonCopyIdentifier = document.getElementById("carbonCopyIdentifier");
                  let carbonCopyInput = carbonCopyIdentifier.querySelector('input');
                  if (carbonCopyInput.checked) {
                    carbonCopyInput.setAttribute("disabled", "disabled");
                    carbonCopyIdentifier.classList.remove("d-none");
                  }

                  buListBox = buListFG.querySelector('select');

                  if (formType[1] === 'Edit to User') {
                      buList.classList.add("d-none");
                      userListBox.removeAttribute("multiple");
                      userListBox.setAttribute("disabled", "disabled");

                  } else if (formType[1] === 'Edit to Business Unit') {
                      userList.classList.add("d-none");
                      buListBox.removeAttribute("multiple");
                      buListBox.setAttribute("disabled", "disabled");
                  }
              }
            } else if (formType[0] === 'Approval Route') {
                buListBox = buListFG.querySelector('input');
                buList.classList.add("d-none");

                userListBox.setAttribute("disabled", "disabled");

                getBusinessUnitUser(buListBox, userListBox, parseInt(userListBox.value));
            }
            myRouteModal.show();
        }

      });
}

function checkUserList(currentItem) {
    let found = 0;
    for(let i = 0; i < recipientLists.length; i++) {
        if (recipientLists[i][0] === currentItem[0] && recipientLists[i][1] === currentItem[1] && recipientLists[i][2] === currentItem[2] && recipientLists[i][3] === currentItem[3]) {
            found += 1;
        }
    }
    return found;
}

function addRecipientToTheList(recipientBox, currentItem, routingUListItems) {
    let items = 0;
    let itemFound = 0;
    if (recipientLists.length === 0) {
        items += 1;
        recipientLists.push(currentItem);
    } else {
        itemFound = checkUserList(currentItem);
        if (itemFound === 0) {
            items += 1;
            recipientLists.push(currentItem);
        }
    }
    if (items > 0) {
        let recipientListItem = document.createElement('li');
        recipientListItem.classList.add("mt-2", "d-flex", "justify-content-around", "align-items-center");
        let index = -1;
        for (let i = 0; i < recipientBox.options.length; i++) {
          if (recipientBox.options[i].value === currentItem[0]) {
            index = i;
            break;
          }
        }
        if (index !== -1) {
            let maxLength = 18;

            if (recipientBox.options[index].text.length > maxLength) {
                recipientListItem.textContent = recipientBox.options[index].text.substring(0, maxLength) + " ...";
                recipientListItem.setAttribute("title", recipientBox.options[index].text);
            } else {
                recipientListItem.textContent = recipientBox.options[index].text
            }
            if (currentItem[4] === true) {
                let ccIcon = document.createElement("i");
                ccIcon.classList.add("bi", "bi-cc-circle-fill", "mr-1", "text-danger", "fw-bolder");
                ccIcon.style.marginLeft = "-5px";
                recipientListItem.insertBefore(ccIcon, recipientListItem.firstChild);
            }
            let closeIcon = document.createElement("i");
            closeIcon.classList.add("bi", "bi-x-circle", "ml-3", "fw-bolder");
            closeIcon.style.marginRight = "-5px";
            recipientListItem.appendChild(closeIcon);


            closeIcon.addEventListener("click", function () {
                recipientListItem.parentNode.removeChild(recipientListItem);
                removeItemFromToUsersList(currentItem);
            });

            routingUListItems.append(recipientListItem);
        }
    }
}

function removeItemFromToUsersList(currentItem) {
    for (let i = 0; i < recipientLists.length; i++) {
        if (recipientLists[i][0] === currentItem[0] && recipientLists[i][1] === currentItem[1] && recipientLists[i][2] === currentItem[2] && recipientLists[i][3] === currentItem[3]) {
            recipientLists.splice(i, 1);
            i -= 1;
        }
    }

}

function addRecipient(recipientBox, selectedOptions, isToExternal, isToBusinessUnit, isToUser, carbonCopy, toAll, routingUListItems) {
    if (toAll) {
        for (let i = 0; i < recipientBox.options.length; i++) {
            let recipientOption =  recipientBox.options[i];
            if (!recipientOption.classList.contains("d-none")) {
                let recipientId = recipientOption.value;
                let currentItem = [recipientId, isToExternal, isToBusinessUnit, isToUser, false];
                addRecipientToTheList(recipientBox, currentItem, routingUListItems)
            }
        }
    } else if (selectedOptions.length > 0) {
        selectedOptions.forEach(item => {
            let currentItem = [item, isToExternal, isToBusinessUnit, isToUser, carbonCopy];
            addRecipientToTheList(recipientBox, currentItem, routingUListItems)
        });
    } else {
        let message = "";
        if (isToExternal) {
            message = "First select External Customer and Click on Add!"
        } else if (isToBusinessUnit) {
            message = "First select Business Unit and Click on Add!"
        } else if (isToUser ) {
            message = "First select User and Click on Add!"
        }
        let toastBg = "bg-danger";
        let toastHeader = 'Error';
        displayToastMessage(message, toastBg, toastHeader);
    }
}

function getBusinessUnitUser(buBox, userBox, currentSelection) {
    let bUnitId = buBox.value;
    if (bUnitId !== "") {
        userBox.innerHTML = '';
        let url = "/organogram/get_bu_users/" + bUnitId;
        fetch(url, {method: 'GET'})
            .then(response => response.json())
            .then(data => {
                let users = JSON.parse(data.users);
                users.forEach(item => {
                    let option = document.createElement("option");
                    option.value = item.id;
                    option.text = item.first_name + " " + item.last_name;
                    // if (item.is_manager || item.is_delegate) {
                    //     option.style.fontWeight = 'bold';
                    // }
                    if (item.id === currentSelection) {
                        option.selected = true;
                    }
                    userBox.appendChild(option);
                });
            });
    }
}

function checkForComboSelection(formType, routingAction, externalListBox, buListBox, userListBox) {
    if (formType[1] === undefined) {
        let isCc = false;
        let memoStatus = document.getElementById("memoStatus");
        if ((memoStatus.value === "draft" || memoStatus.value === "approved") && routingAction !== 'Send External Memo') {
            let carbonCopy = document.getElementById('carbonCopy');
            let carbonCopyCheckBox = carbonCopy.querySelector('input');

            isCc = carbonCopyCheckBox.checked;
        }
        if (recipientLists.length === 0) {
            if (externalListBox.value !== '') {
                let externalId = externalListBox.options[externalListBox.selectedIndex].value;
                let currentItem = [externalId, true, false, false, isCc];
                let found = checkUserList(currentItem);
                if (found === 0) {
                    recipientLists.push([externalId, true, false, false, isCc]);
                }
            }
            if (buListBox.value !== '') {
                let bunitId = buListBox.options[buListBox.selectedIndex].value;
                let currentItem = [bunitId, false, true, false, isCc];
                let found = checkUserList(currentItem);
                if (found === 0) {
                    recipientLists.push([bunitId, false, true, false, isCc]);
                }
            }
            if (userListBox.value !== '') {
                let userId = parseInt(userListBox.options[userListBox.selectedIndex].value);
                let currentItem = [userId, false, false, true, isCc];
                let found = checkUserList(currentItem);
                if (found === 0) {
                    recipientLists.push([userId, false, false, true, isCc]);
                }
            }
        }
    }
    else {
        let carbonCopyIdentifier = document.getElementById("carbonCopyIdentifier");
        let ccCheckBox = carbonCopyIdentifier.querySelector('input');
        let isCc = ccCheckBox.checked;
        if (formType[1] === 'Edit to User') {
            let userId = parseInt(userListBox.value);
            let currentItem = [userId, false, false, true, isCc];
            let found = checkUserList(currentItem);

            if (found === 0) {
                recipientLists.push([userId, false, false, true, isCc]);
            }
        } else if (formType[1] === 'Edit to Business Unit') {
            let bunitId = buListBox.options[buListBox.selectedIndex].value;
            let currentItem = [bunitId, false, true, false, isCc];
            let found = checkUserList(currentItem);

            if (found === 0) {
                recipientLists.push([bunitId, false, true, false, isCc]);
            }
        } else if (formType[1] === 'Edit to External') {
            let externalId = externalListBox.options[externalListBox.selectedIndex].value;
            let currentItem = [externalId, false, true, false, isCc];
            let found = checkUserList(currentItem);

            if (found === 0) {
                recipientLists.push([externalId, true, false, false, isCc]);
            }
        }
    }
}

function buildToUserList(form, routingAction, externalListBox, buListBox, userListBox) {
    let formData = new FormData(form);
    let toExternalList = [];
    let toUserList = [];
    let toBuList = [];
    let toBuCcList = [];
    let toCcList = [];
    let toExternalCcList = [];
    let formTypeInput = document.getElementById('formType');
    let formType = formTypeInput.value.split('-');
    if (formType[0] === 'Memo Route') {
        checkForComboSelection(formType, routingAction, externalListBox, buListBox, userListBox);

        for (let i = 0; i < recipientLists.length; i++){
            if (recipientLists[i][1] === true) {
                toExternalList.push(recipientLists[i][0]);
                toExternalCcList.push(recipientLists[i][4]);
            } else if (recipientLists[i][2] === true) {
                formData.set("business_unit", recipientLists[i][0]);
                toBuList.push(recipientLists[i][0]);
                toBuCcList.push(recipientLists[i][4]);
            } else if (recipientLists[i][3] === true) {
                toUserList.push(recipientLists[i][0]);
                toCcList.push(recipientLists[i][4]);
            }
        }
    } else {
        toUserList.push(formData.get("to_user"));
        toCcList.push(formData.get("carbon_copy"));
    }

    formData.set("to_user_list", toUserList.toString());
    formData.set("to_bu_list", toBuList.toString());
    formData.set("to_external_list", toExternalList.toString());
    formData.set("carbon_copy_list", toCcList.toString());
    formData.set("bu_carbon_copy_list", toBuCcList.toString());
    formData.set("external_carbon_copy_list", toExternalCcList.toString());

    return formData;
}

function routeSubmit(formId, url, myModal, routingAction, externalListBox, buListBox, userListBox) {
    let submitBtn = document.querySelector(`#${formId}`);

    if (submitBtn != null) {
        let routingFormBtns = submitBtn.querySelector('#routingFormBtns');
        let btnSubmit = routingFormBtns.querySelector('button');
        submitBtn.addEventListener('submit', function (event) {
            event.preventDefault();
            if (externalListBox.value !== '' || buListBox.value !== '' || userListBox.value !== '' || recipientLists.length > 0) {
                let formData = buildToUserList(this, routingAction, externalListBox, buListBox, userListBox);
                btnSubmit.setAttribute("disabled", "disabled");
                acceptPIN('accept_pin',  'PIN Code', 'route');
                disableEnablePinContinue();

                let pinCode = document.getElementById('id_pin_code');
                let confirmPinCode = document.getElementById('confirmPinCode');

                if (confirmPinCode) {
                    confirmPinCode.addEventListener('click', function(event) {
                        event.preventDefault();
                        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                        console.log("CSRFToken: " + csrftoken);
                        fetch('/user/accept_pin/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrftoken
                            },
                            body: JSON.stringify({"pin": pinCode.value})
                        }).then(response => response.json())
                            .then(data => {
                                if (data.message === 'success') {
                                    fetch(url, {
                                            method: 'POST',
                                            body: formData
                                        }).then (response => response.json())
                                            .then(data => {
                                                if (data.message === 'success') {
                                                    let message = 'You have successfully sent Memo to the recipient(s)!';
                                                    let toastBg = "bg-info";
                                                    let toastHeader = 'Success';
                                                    btnSubmit.removeAttribute("disabled");
                                                    displayToastMessage(message, toastBg, toastHeader);
                                                    $('#pinCodeModal').modal('hide');
                                                    closePinCodeModal();
                                                    myModal.hide();
                                                } else {
                                                    let message = data.message;
                                                    let toastBg = "bg-danger";
                                                    let toastHeader = 'Error';
                                                    btnSubmit.removeAttribute("disabled");
                                                    displayToastMessage(message, toastBg, toastHeader);
                                                }
                                            }).catch(error => {
                                                let message = 'Server Error : ' + error;
                                                let toastBg = "bg-danger";
                                                let toastHeader = 'Error';
                                                btnSubmit.removeAttribute("disabled");
                                                displayToastMessage(message, toastBg, toastHeader);
                                        });
                                } else {
                                    $('#pinCodeModal').modal('hide');
                                    closePinCodeModal();

                                    btnSubmit.removeAttribute("disabled");
                                    let message = 'The PIN Code you provided is incorrect try again!!!';
                                    let toastBg = "bg-danger";
                                    let toastHeader = 'Error';
                                    displayToastMessage(message, toastBg, toastHeader);
                                    btnSubmit.removeAttribute("disabled");
                                }
                            });
                    });
                }
            } else {
                let message = 'Please select at least one recipient!';
                let toastBg = "bg-danger";
                let toastHeader = 'Error';
                displayToastMessage(message, toastBg, toastHeader);
            }
        });
    }
}

function displayToastMessage(message, toastBg, toastHeader) {
    const toastLiveExample = document.getElementById('generalToast');
    const toast_body = document.getElementById('id_toast_body');
    const toast_header = document.getElementById('id_toast_header');
    let toastIconContainer = toastLiveExample.querySelector(".toast-header");
    let toastIcon = toastIconContainer.querySelector('i');

    const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastLiveExample);

    toastLiveExample.classList.add(toastBg);
    toastIcon.classList.add("bi-exclamation-triangle-fill");
    toast_body.textContent = message;
    toast_header.textContent = toastHeader;
    toastBootstrap.show();

    if (toastHeader === 'Success') {
        setTimeout(function() {
          window.location.reload();
        }, 500);
    }
}

function sendMemo(formId, myModal, createMemoForm, routingAction, externalListBox, buListBox, userListBox) {
    let submitBtn = document.querySelector(`#${formId}`);
    let sendMemo = document.getElementById('sendMemo');
    let routingFormBtns = submitBtn.querySelector('#routingFormBtns');
    let btnSubmit = routingFormBtns.querySelector('button');

    createMemoForm.addEventListener('submit', function(event) {
        event.preventDefault();
        let formData = buildToUserList(submitBtn, routingAction, externalListBox, buListBox, userListBox);

        let memoFormData = new FormData(createMemoForm);

        if (routingAction === 'Send Memo' || routingAction === 'Send External Memo') {
            memoFormData.set("send_memo", "");
        }

        if (routingAction === 'Send Approval') {
            memoFormData.set("approval_send", "");
        }

        formData.forEach((value, key) => {
            memoFormData.append(key, value);
        });

        fetch(createMemoForm.action, {
            method: 'POST',
            body: memoFormData
        }).then (response => response.json())
            .then(data => {
                if (data.message === 'success') {
                    let message = 'You have successfully sent Memo to the recipient(s)!';
                    let toastBg = "bg-info";
                    let toastHeader = 'Success';
                    btnSubmit.removeAttribute("disabled");
                    displayToastMessage(message, toastBg, toastHeader);
                    myModal.hide();
                } else {
                    let toastBg = "bg-danger";
                    let toastHeader = 'Error';
                    btnSubmit.removeAttribute("disabled");
                    displayToastMessage(data.message, toastBg, toastHeader);
                }
            }).catch(error => {
                let message = 'Error saving routing information:- ' + error;
                let toastBg = "bg-danger";
                let toastHeader = 'Error';
                btnSubmit.removeAttribute("disabled");
                displayToastMessage(message, toastBg, toastHeader);
        });
    });

    submitBtn.addEventListener('submit', function (event) {
        event.preventDefault();
        if (externalListBox.value !== '' || buListBox.value !== '' || userListBox.value !== '' || recipientLists.length > 0) {
            btnSubmit.setAttribute("disabled", "disabled");
            acceptPIN('accept_pin',  'PIN Code', 'route');
            disableEnablePinContinue();

            let pinCode = document.getElementById('id_pin_code');
            let confirmPinCode = document.getElementById('confirmPinCode');

            if (confirmPinCode) {
                confirmPinCode.addEventListener('click', function(event) {
                    event.preventDefault();
                    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    fetch('/user/accept_pin/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrftoken
                            },
                            body: JSON.stringify({"pin": pinCode.value})
                    }).then(response => response.json())
                        .then(data => {
                            if (data.message === 'success') {
                                sendMemo.click();
                            } else {
                                $('#pinCodeModal').modal('hide');
                                closePinCodeModal();

                                btnSubmit.removeAttribute("disabled");
                                let message = 'The PIN Code you provided is incorrect try again!!!';
                                let toastBg = "bg-danger";
                                let toastHeader = 'Error';
                                displayToastMessage(message, toastBg, toastHeader);
                                btnSubmit.removeAttribute("disabled");
                            }
                        });
                });
            }
        } else {
            let message = 'Please select at least one recipient!';
            let toastBg = "bg-danger";
            let toastHeader = 'Error';
            displayToastMessage(message, toastBg, toastHeader);
        }
    });
}

$('#routeModal').on('hidden.bs.modal', function () {
  $('.modal-backdrop').remove();
});

function acceptPIN(url, title, caller) {
    fetch(url)
        .then(response => response.text())
        .then(content => {
            const temp1Container = document.createElement('div');
            temp1Container.innerHTML = content;
            const pinCodeModal = new bootstrap.Modal(document.getElementById('pinCodeModal'));
            const myRoute1Modal = new bootstrap.Modal(document.getElementById('routeModal'));
            const modal1Title = document.getElementById(('pinCodeModalLabel'));
            const modalCaller = document.getElementById('modalCaller');
            modal1Title.innerHTML = title;
            $('#pinCodeModal').on('shown.bs.modal', function () {
              let input = $('#id_pin_code');
              input.attr('type', 'password');
              input.val('').focus();
              let icon = $('#pin-modal');
              icon.removeClass('bi-eye-slash-fill');
              icon.addClass('bi-eye-fill');
              modalCaller.innerHTML = caller;
            });
            myRoute1Modal.hide();
            pinCodeModal.show();
        });
}

function disableEnablePinContinue() {
    let pinCode = document.getElementById('id_pin_code');
    let confirmPinCode = document.getElementById('confirmPinCode');

    if (pinCode) {
        pinCode.addEventListener('input', function(event) {
            event.preventDefault();
            if (pinCode.value.length >= 4) {
                confirmPinCode.removeAttribute("disabled");
            } else {
                confirmPinCode.setAttribute("disabled", "disabled");
            }
        });
    }
}

function restrictToInteger(event, pinErrorId) {
    if (event.currentTarget.value.length < 4) {
        let charCode = event.which ? event.which : event.keyCode;
        let pinError = document.querySelector(`#${pinErrorId}`);
        if (charCode < 48 || charCode > 57) {
            event.preventDefault();
            pinError.classList.remove("invalid-feedback");
            return false;
        }
        pinError.classList.add("invalid-feedback");
        return true;
    } else {
        return false;
    }
}

function togglePasswordVisibility(id, iconId) {
    let pinInput = document.querySelector(`#${id}`);
    let pinToggle = document.querySelector(`#${iconId}`);

    if (pinInput.type === "password") {
        pinInput.type = "text";
        pinToggle.classList.remove("bi-eye-fill");
        pinToggle.classList.add("bi-eye-slash-fill");
    } else {
        pinInput.type = "password";
        pinToggle.classList.remove("bi-eye-slash-fill");
        pinToggle.classList.add("bi-eye-fill");
    }
}

function closePinCodeModal() {
    const modalCaller = document.getElementById('modalCaller');
    if (modalCaller.innerHTML === "route") {
        const myRouteModal = new bootstrap.Modal(document.getElementById('routeModal'));
        myRouteModal.show();

        let routingFormBtns = myRouteModal._element.querySelector('#routingFormBtns');
        let btnSubmit = routingFormBtns.querySelector('button');
        btnSubmit.removeAttribute("disabled");
    }
}

function addCustomer(url, form_id, title) {
    fetch(url)
        .then(response => response.text())
        .then(content => {
            const temp1Container = document.createElement('div');
            temp1Container.innerHTML = content;
            const form1Element = temp1Container.querySelector(`#${form_id}`);
            const myCustomerModal = new bootstrap.Modal(document.getElementById('customerModal'));
            const myRouteModal = new bootstrap.Modal(document.getElementById('routeModal'));
            if (form1Element) {
                const modal1Title = document.getElementById(('customerModalLabel'));
                modal1Title.innerHTML = title;
                const modal1Body = document.getElementById('customerModalBody');
                modal1Body.innerHTML = '';
                modal1Body.appendChild(form1Element);
                myCustomerModal._dialog.classList.remove("modal-lg");
                myCustomerModal._dialog.classList.add("modal");
                myRouteModal.hide();
                myCustomerModal.show();

                saveCustomer(form_id, myCustomerModal, form1Element);
            }
        });
}

function closeCustomerModal() {
    const myRouteModal = new bootstrap.Modal(document.getElementById('routeModal'));
    myRouteModal.show();
}

function saveCustomer(form_id, myCustomerModal, form1Element) {
    const myRouteModal = new bootstrap.Modal(document.getElementById('routeModal'));
    form1Element.addEventListener('submit', function (event) {
        event.preventDefault();
        let customerFormData = new FormData(form1Element);
        fetch('/organogram/add_new_customer/routing', {
            method: 'POST',
            body: customerFormData
        }).then(response => response.json())
            .then(data => {
                if (data.message === 'success') {
                    let externalListFG = document.querySelector('#externalList .form-group');
                    let externalListBox = externalListFG.querySelector('select');
                    let optionElement = document.createElement('option');

                    optionElement.value = data.customer_id;
                    optionElement.text = data.customer_name;
                    externalListBox.appendChild(optionElement);

                    myRouteModal.show();
                }
            });
    })
}
