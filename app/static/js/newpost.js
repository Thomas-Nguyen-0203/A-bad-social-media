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

async function processPost() {
    var title = document.getElementById("title").value;

    let empty = 0;

    if (title.length == 0 || title.trim().length == 0)
    {
      document.getElementById("title_err").innerHTML = "<b>This field cannot be empty</b>";
      empty = 1;
    }
    else
        document.getElementById("title_err").innerHTML = "";
  
    var postInfo = document.getElementById("postinfo").value;

    if (postInfo.length == 0 || postInfo.trim().length == 0)
    {
      document.getElementById("content_err").innerHTML = "<b>This field cannot be empty</b>";
      empty = 1;
    }
    else
      document.getElementById("content_err").innerHTML = "";

    if (empty)
        return;

    let postUrl = document.location.href;

    try{
      let response = await fetch(
        postUrl,
        {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            title: title,
            content: postInfo
          })
        }
      );
    
      let json_response = await response.json();

      if (json_response["isMuted"])
        muteAlert();
      else
        window.open(json_response["URL"], "_self")
        
        

    } catch (e)
    {
      console.error(e.message);
    }    
}