function amountDelete(url) {
  const request = new XMLHttpRequest()
  request.open('POST', url, true)
  request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));

  request.onload = function() {
    const resp = this.response
    if (this.status >= 200 && this.status < 400) {
      // Success!
      location.reload()
    } else {
      // We reached our target server, but it returned an error
      alert("It broke horribly.  Next popup will be whatever ugly results.")
      alert(resp)
    }
  }

  request.onerror = function() {
    // There was a connection error of some sort.
    // Just try again forever whatever.
    amountDelete(url)
  }

  request.send()
}

function amountSave(url, name, monthNumber) {
  const request = new XMLHttpRequest()
  request.open('POST', url, true)
  request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
  request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")

  request.onload = function() {
    const resp = this.response
    if (this.status >= 200 && this.status < 400) {
      // Success!
      // TODO: Remove this one from GET.
      location.reload()
    } else {
      // We reached our target server, but it returned an error
      alert("It broke horribly.  Next popup will be whatever ugly results.")
      alert(resp)
    }
  }

  request.onerror = function() {
    // There was a connection error of some sort.
    // Just try again forever whatever.
    amountSave(url, name, monthNumber)
  }

  request.send(
    "amount=" + document.getElementById(name).value + "&month=" + monthNumber
  )
}
