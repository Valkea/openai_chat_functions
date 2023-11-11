/*
Description: This script provides a javascript interface connecting to the inference API (API_serving) and display the result on the HTML page.
Author: Letremble Emmanuel (emmanuel+code@shedge.com)
*/


// --- GLOBAL VARIABLES ---

const currentUrl = window.location.href;
const splitUrl = currentUrl.split("5000");
let api_url = "http://127.0.0.1:5000/";

if(currentUrl != splitUrl){
	api_url = splitUrl[0]+"5000/"
}

// --- INIT ---

window.onload = function() {

	var submitBtn = document.getElementById('submit-query');
	submitBtn.addEventListener('click', function (event) {
		sendContent()
	});

	var submitInput = document.getElementById('query');
	submitInput.addEventListener('keypress', function (event) {
		if (event.key === "Enter") {
			sendContent()
		}
	});
}


// --- FUNCTIONS

const RETRY_COUNT = 5;
async function fetchRetry(...args) {
	let count = RETRY_COUNT;
  	while(count > 0) {
    		try {
      			return await fetch(...args);
    		} catch(error) {
			console.error('error:', error)
		}
    		count -= 1;
  	}

	throw new Error(`Too many retries`);
}

function sendContent() {

	url = api_url + "inference"
	console.log("We are infering on "+url)
	callback_id = 'chat_answer'
	content = document.getElementById("query").value;

	appendMessage('USER', 'user.svg', 'right', content)
	document.getElementById("query").value = ""

	let formData = new FormData();
    	formData.append("query", content);

	var myInit = {
		method: 'POST',
	    	headers: new Headers(),
	    	// cache: 'default',
	    	// mode: 'cors',
	    	body: formData
    	}

    	return fetchRetry( url, myInit )
    	.then( response => response.json() )
    	.then( json => callback(json, callback_id) )
    	.catch( error => console.error('error:', error) );
}

function callback(json, callback_id) {

	myObj = JSON.stringify(json);
	// document.getElementById(callback_id).innerHTML = myObj;
	console.log(myObj)
	// var source = document.getElementById('blueprint_user')
	//
	appendMessage('BOT', 'bot.svg', 'left', myObj)
}

function appendMessage(name, img, side, text) {
	const msgHTML = `
    		<div class="msg ${side}-msg">
      			<div class="msg-img" style="background-image: url(medias/${img})"></div>
		        <div class="msg-bubble">
        			<div class="msg-info">
          				<div class="msg-info-name">${name}</div>
          				<div class="msg-info-time">${formatDate(new Date())}</div>
        			</div>
        			<div class="msg-text">${text}</div>
      			</div>
    		</div>`;

	msgerChat = document.querySelector(".msger-chat")
  	msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  	msgerChat.scrollTop += 500;
}

function formatDate(date) {
	const h = "0" + date.getHours();
  	const m = "0" + date.getMinutes();

  	return `${h.slice(-2)}:${m.slice(-2)}`;
}

