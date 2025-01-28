function toggleText() {
  var header = document.querySelector('.header');

  if (header.innerHTML === 'Memo') {
    header.innerHTML = 'DMS';
  } else {
    header.innerHTML = 'Memo';
  }
}


