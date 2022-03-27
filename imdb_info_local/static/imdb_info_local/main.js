

function setupResultsListButtons() {
    /*  Click on the ratings/title div to expose the links to all titles in search */
    titleDivs = document.getElementsByClassName('title-rating');
    console.log('titleDivs: ' + titleDivs.length);
    for (let i=0; i<titleDivs.length; i++) {
        titleDivs[i].addEventListener('click', function(e){
            let mainContent = e.target.closest('.main-content');
            let title = mainContent.dataset.title;
            let videoType = mainContent.dataset.videoType;
            let updateUrl = mainContent.dataset.updateUrl;
            let findResults = mainContent.nextElementSibling;
            findResults.classList.toggle('hidden');
            /* When the found titles list is opened add buttons to allow changing the info */
            /* for the title to that button's title data */
            if (!findResults.classList.contains('hidden')) {
                if (!findResults.querySelector('button')) {
                    Array.from(findResults.querySelectorAll('li')).forEach((e) => {
                        let imdbTitleUrl = e.firstChild['href'];
                        let btn = document.createElement('button');
                        btn.type = 'button';
                        btn.innerText = 'Use This Instead';
                        // btn.style.marginRight = '1em';
                        btn.classList.add('button');
                        btn.addEventListener('click', btnEv => {
                            postUpdate(title, updateUrl, imdbTitleUrl, videoType, mainContent, btn);
                        });
                        e.insertBefore(btn, e.firstChild);
                    });
                    /* Add a button and text input for user to input a title url as a last resort
                     */
                    let li = document.createElement('li');
                    let txtBox = document.createElement('input');
                    txtBox.type = 'url';
                    // txtBox.size = 50;

                    let btn = document.createElement('button');
                    btn.type = 'button';
                    btn.innerText = 'Use Title URL';
                    btn.classList.add('button');
                    btn.addEventListener('click', btnEv => {
                        let titleUrl = txtBox.value;
                        console.log('titleUrl: ' + titleUrl);
                        postUpdate(title, updateUrl, titleUrl, videoType, mainContent, btn);
                        txtBox.value = '';
                    });
                    li.append(btn, txtBox);
                    findResults.firstElementChild.appendChild(li);
                }
            }
        });
    }
}

/**
 * Show or remove font-awesome spinner from button
 *
 * @param btn - button to add spinner to
 */
function handleLoadingDisplay(btn) {
    if (btn.querySelector('i')) {
        btn.removeChild(btn.querySelector('i'));
    } else {
        let iElem = document.createElement('i');
        iElem.classList.add('fa', 'fa-spinner', 'fa-spin');
        btn.insertBefore(iElem, btn.firstChild);
    }
}

function refreshImage(imageDiv, newUrl) {
    let oldImg = imageDiv.querySelector('img');
    let oldImgUrl = new URL(oldImg.src);
    let imgHeight = oldImg.height;
    let newImgUrl = new URL(`${oldImgUrl.protocol}//${oldImgUrl.host}${newUrl}`);
    console.log(`old image src: ${oldImgUrl}`);
    imageDiv.removeChild(imageDiv.firstElementChild);
    let newImg = document.createElement('img');
    newImg.src = newImgUrl.href;
    newImg.height = imgHeight;
    console.log(`new image src: ${newImgUrl}`);
    imageDiv.appendChild(newImg);
}

function refreshRatingAndBlurb(title, titleContentDiv, newRating, newBlurb) {
    let titleRatingDiv = titleContentDiv.querySelector('.title-rating');
    let blurbDiv = titleContentDiv.querySelector('.blurb');
    console.log(`new rating/blurb: ${newRating} ${newBlurb}`);
    titleRatingDiv.removeChild(titleRatingDiv.firstElementChild);
    let titleRatingP = document.createElement('p');
    titleRatingP.textContent = `${newRating} - ${title}`;
    titleRatingDiv.appendChild(titleRatingP);
    blurbDiv.removeChild(blurbDiv.firstElementChild);
    let blurbP = document.createElement('p');
    blurbP.innerHTML = newBlurb;
    blurbDiv.appendChild(blurbP);
}

function postUpdate(title, updateUrl, imdbTitleUrl, videoType, titleContentDiv, loadBtn) {
    console.log(`url: ${imdbTitleUrl}  title: ${title} type: ${videoType}`);
    let csrftoken = getCookie('csrftoken');
    console.log(`csrftoken: ${csrftoken}`)
    // if (csrftoken === null) {
    //     alert('The csrftoken is null - cookies must be allowed. (Private window?)');
    // }
    handleLoadingDisplay(loadBtn);
    const timeLimit = 10000;
    const controller = new AbortController();
    const timeout = setTimeout(() => {
        controller.abort();
    }, timeLimit);

    /* Post request to update the title info - rescraping IMdb and updating db */
    fetch(updateUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({'post_data': {
                'title': title,
                'url': imdbTitleUrl,
                'video_type': videoType
            }}),
        signal: controller.signal
    })
        .then(response => {
            if (!response.ok) {
                if (response.status === 403 && csrftoken === null) {
                    throw new Error('403: The csrftoken is null - cookies must be allowed. (Private window?)');
                } else {
                    throw new Error(`${response.status}: ${response.statusText}`);
                }
            }
            return response.json()
        })
        .then(data => {
            if ('error' in data) {
                throw new Error(data['error']);
            } else {
                refreshRatingAndBlurb(title, titleContentDiv, data['rating'], data['blurb']);
                refreshImage(titleContentDiv.querySelector('.title-image'), data['image-url']);
            }
        })
        .catch(error => {
            if (error.name === 'AbortError') {
                alert('Timeout updating from IMdb.');
            } else {
                alert(error);
            }
        })
        .finally(() => handleLoadingDisplay(loadBtn));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

setupResultsListButtons();

searchBox = document.querySelector('input');
searchBox.value = '';
