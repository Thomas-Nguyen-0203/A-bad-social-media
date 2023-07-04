const sidebar = document.querySelector(".largerbox");
const comment = document.getElementById("comment")

let position = localStorage.getItem(window.location.href + "cursor");
if (position !== null) 
    sidebar.scrollTop = parseInt(position, 10);

let prevComment = localStorage.getItem(window.location.href + "comment");

if (prevComment !== null && prevComment.trim().length != 0)
    comment.value = prevComment;

window.addEventListener("beforeunload", () => {
  localStorage.setItem(window.location.href + "cursor", sidebar.scrollTop);
  if (comment.value.length != 0)
    localStorage.setItem(window.location.href + "comment", comment.value);
});


function removeMutedAlert()
{
    document.getElementById("mutedalertbox").style.display = "none";
}

function muteAlert()
{
  document.getElementById("mutedalertbox").style.display = "block";
  setTimeout(removeMutedAlert, 5000);
}

document.getElementById("closemutedalert").addEventListener(
  "click", removeMutedAlert
);

async function processComment() {

    var comment_made = document.getElementById("comment").value;

    if (comment_made.length == 0 || comment_made.trim().length == 0)
    {
        document.getElementById("comment_err").innerHTML = "<b>This field cannot be empty</b>";
        return;
    }

    document.getElementById("comment_err").innerHTML = "";
    const COMMENT_URL = window.location.href + "/comment";

    try
    {
        let response = await fetch(
            COMMENT_URL,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    content: comment_made
                })
            }
        );

        let response_json = await response.json();
    
        localStorage.removeItem(window.location.href+"comment");

        if (response_json["isMuted"])
        {
            muteAlert();
        }
            
        else
        {
            comment.value = "";
            location.reload();
        }
            

    } catch (e)
    {
        console.error(e.message);
    }
} 


const UPVOTE_URL = document.location.href + "/upvote";
const DOWNVOTE_URL = document.location.href + "/downvote";

document.getElementById("upvote").addEventListener("mousedown", async() =>{
    
    let response = await fetch(
        UPVOTE_URL,
        {
            method: "POST"
        }
    );

    if (response.redirected)
    {
        window.open(response.url, "_self");
    }
    
    window.location.reload();
})

document.getElementById("downvote").addEventListener("mousedown", async() =>{
    
    let response = await fetch(
        DOWNVOTE_URL,
        {
            method: "POST"
        }
    );

    if (response.redirected)
    {
        window.open(response.url, "_self");
    }
    
    window.location.reload();
})