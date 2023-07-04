const SUBTLE = window.crypto.subtle;

const SUBMIT_BUTTON = document.getElementById("submit");
const CHATBOX = document.getElementById("chatbox");
const FETCH_URL = document.location.href + "/messages";
const SOCKET_URL = document.location.href.replace("https", "wss") + "/messages";

const SOCK = new WebSocket(SOCKET_URL);

const MONTH_MAP = new Map([
    [0, "Jan"],
    [1, "Feb"],
    [2, "Mar"],
    [3, "Apr"],
    [4, "May"],
    [5, "Jun"],
    [6, "Jul"],
    [7, "Aug"],
    [8, "Sep"],
    [9, "Oct"],
    [10, "Nov"],
    [11, "Dec"]
]);
const IV_LENGTH = 3;
const HMAC_LENGTH = 256/8;

function dateFormatting(epochStamp)
{
    /**
     * This function returns the timestamp in the format of
        Aug 03, 13:03:12
    */
    let timestamp = new Date(epochStamp);

    return `${MONTH_MAP.get(timestamp.getMonth())} ${timestamp.getDate()}, 
    ${timestamp.getHours()}:${('0'+timestamp.getMinutes()).slice(-2)}`
}

function addNewMsg(msg, side, senderName, time)
{ 
    /**
     * This function dynamically adds new messages to the chat box.
     */
    // Generating html for message info.
    let msgInfo = document.createElement("div");
    msgInfo.className = "msg-info";

    let name = document.createElement("div");
    name.className = "msg-info-name";
    name.textContent = senderName;

    let timestamp = document.createElement("div");
    timestamp.className = "msg-info-time";
    timestamp.textContent = dateFormatting(time);

    if (side == "left")
    {
        msgInfo.appendChild(name);
        msgInfo.appendChild(timestamp);
    }
    else
    {
        msgInfo.appendChild(timestamp);
        msgInfo.appendChild(name);
    }

    // Generating html for message
    let messageHTML = document.createElement("div");
    messageHTML.className = `${side}message`;

    let messageContent = document.createElement("p");
    messageContent.textContent = msg.trim();

    messageHTML.appendChild(messageContent);
    
    // Generate the final outer div.
    let outerDiv = document.createElement("div");
    outerDiv.className = `${side}-bubble`;
    outerDiv.appendChild(msgInfo);
    outerDiv.appendChild(messageHTML);

    CHATBOX.appendChild(outerDiv);
    CHATBOX.scrollTop += 70;
}

async function encrypt(key, msg, params)
{
    /**
    * This function encrypts msg with the given key and params.
    * Note, the msg must be encoded before passing in
    */
    let result = null;
    try{
        result = await SUBTLE.encrypt(
            params,
            key,
            msg
        );
    } catch (e)
    {
        console.log(e);
    }
    
    return result
}

async function decryptAndVerify(key, msg)
{
    /**
     * This function first verifies the message then decrypts it.
    */
    const DECODER = new TextDecoder();
    msg = JSON.parse(msg);

    const ENC_SYMKEY_OBJ = JSON.parse(msg["key"]);
    const KEY_DIGITS = Object.keys(ENC_SYMKEY_OBJ);
    let encryptedSymKey = new Uint8Array(KEY_DIGITS.length);

    let i = 0;
    for (index in KEY_DIGITS)
        encryptedSymKey[i++] = ENC_SYMKEY_OBJ[index];

    let symkeyJWK = await SUBTLE.decrypt(
        {
            name: "RSA-OAEP"
        },
        key,
        encryptedSymKey
    );

    symkeyJWK = JSON.parse(DECODER.decode(symkeyJWK));

    const ACTUAL_SYMKEY = await SUBTLE.importKey(
        "jwk",
        symkeyJWK,
        {name: "AES-GCM"},
        false,
        ["decrypt"]
    );

    const LENGTH = msg["length"];

    let encryptedDataObj = JSON.parse(msg["data"]);
    let encryptedData = new Uint8Array(LENGTH);
    for (i = 0; i < LENGTH; i++)
        encryptedData[i] = encryptedDataObj[`${i}`];

    const ivObj = JSON.parse(msg["iv"]);
    let iv = new Uint32Array(IV_LENGTH);
    for (i = 0; i < 3; i++)
        iv[i] = ivObj[`${i}`];

    const ENCRYPTED_CONTENT = new Uint8Array(await SUBTLE.decrypt(
        {
            name: "AES-GCM",
            iv: iv
        },
        ACTUAL_SYMKEY,
        encryptedData
    ));

    const ENC_HMAC_KEY = JSON.parse(msg["hmac_key"]);
    const HMAC_KEY_LENGTH = msg["hmac_key_length"]
    let encryptedHmacKey = new Uint8Array(HMAC_KEY_LENGTH);

    for (i = 0; i < HMAC_KEY_LENGTH; i++)
        encryptedHmacKey[i] = ENC_HMAC_KEY[`${i}`];

    let hmacKeyJWK = await SUBTLE.decrypt(
        {
            name: "RSA-OAEP"
        },
        key,
        encryptedHmacKey
    );    
    hmacKeyJWK = JSON.parse(DECODER.decode(hmacKeyJWK));

    const ACTUAL_HMAC_KEY = await SUBTLE.importKey(
        "jwk",
        hmacKeyJWK,
        {
            name: "HMAC",
            hash: "SHA-256"
        },
        false,
        ["sign", "verify"]
    );
    
    const MSG_LENGTH = ENCRYPTED_CONTENT.length - HMAC_LENGTH;
    const MESSAGE = ENCRYPTED_CONTENT.slice(0, MSG_LENGTH);
    const SIGNATURE = ENCRYPTED_CONTENT.slice(MSG_LENGTH, ENCRYPTED_CONTENT.length);


    const VERIFIED = await SUBTLE.verify(
        "HMAC",
        ACTUAL_HMAC_KEY,
        SIGNATURE,
        MESSAGE
    );

    return {message: DECODER.decode(MESSAGE), verification: VERIFIED};
}

async function main()
{
    const publicKey =  await SUBTLE.importKey(
        "jwk",
        pubKeyJSON,
        {
            name: "RSA-OAEP",
            hash: "SHA-256"
        },
        false,
        ["encrypt"]
    );

    const decryptKey = await SUBTLE.importKey(
        "jwk",
        JSON.parse(window.localStorage.getItem("private_key")),
        {
            name: "RSA-OAEP",
            hash: "SHA-256"
        },
        false,
        ["decrypt"]
    )

    const symKeyObj = await SUBTLE.generateKey(
        {
            name: "AES-GCM",
            length: 256 
        },
        true,
        ["encrypt", "decrypt"]
    );

    const hmacKey = await SUBTLE.generateKey(
        {
            name: "HMAC",
            hash: "SHA-256"
        },
        true,
        ["sign", "verify"]
    );

    const exportedHmacKey = JSON.stringify(await SUBTLE.exportKey(
        "jwk",
        hmacKey
    ));

    const exportedSymKey = JSON.stringify(await SUBTLE.exportKey(
        "jwk",
        symKeyObj
    ));
    
    SUBMIT_BUTTON.addEventListener("mousedown", async () => {
        const TEXT_ENCODER = new TextEncoder();

        const CONTENT = document.getElementById("content").value.trim();
    
        if (SOCK.readyState != SOCK.OPEN)
            return;
    
        if (CONTENT.length == 0)
            return;
        document.getElementById("content").value = "";
    
        const TIME_STAMP = Date.now()
        addNewMsg(CONTENT, "right", senderName, TIME_STAMP);

        const ENCODED_MSG = TEXT_ENCODER.encode(CONTENT);

        const SIGNATURE = new Uint8Array(await SUBTLE.sign(
            "HMAC",
            hmacKey,
            ENCODED_MSG
        ));

        const FINAL_MESSAGE = new Uint8Array(SIGNATURE.length + ENCODED_MSG.length);

        for (i = 0; i < FINAL_MESSAGE.length; i++)
        {
            if (i >= ENCODED_MSG.length)
                FINAL_MESSAGE[i] = SIGNATURE[i - ENCODED_MSG.length];

            else
                FINAL_MESSAGE[i] = ENCODED_MSG[i];
                // Simulating ciphertext being modified
                // FINAL_MESSAGE[i] = 1
        }

        let initVector = window.crypto.getRandomValues(
            new Uint32Array(IV_LENGTH)
        );

        initVector[0] = userId;

        let encryptedMsg = new Uint8Array(
            await encrypt(
                symKeyObj, FINAL_MESSAGE, {name: "AES-GCM", iv: initVector}
            )
        );

        let encryptedSymKey = new Uint8Array(
            await encrypt(
                publicKey,
                TEXT_ENCODER.encode(exportedSymKey),
                {
                    name: "RSA-OAEP"
                }
            )
        );
        
        let encryptedHmacKey = new Uint8Array(
            await encrypt(
                publicKey,
                TEXT_ENCODER.encode(exportedHmacKey),
                {
                    name: "RSA-OAEP"
                }
            )
        )
    
        SOCK.send(JSON.stringify(
            {
            method: "POST",
            content: JSON.stringify(
                {
                    data: JSON.stringify(encryptedMsg),
                    length: encryptedMsg.length,
                    key: JSON.stringify(encryptedSymKey),
                    iv: JSON.stringify(initVector),
                    hmac_key: JSON.stringify(encryptedHmacKey),
                    hmac_key_length: encryptedHmacKey.length
                }
            ),
            timestamp: TIME_STAMP
            }
        ));
    });
    
    document.getElementById("main_chat").addEventListener("keydown", (event) => {
        if (event.key == "Enter")
        {
            event.preventDefault()
            if (!event.shiftKey)
            {
                const event = new Event("mousedown");
                SUBMIT_BUTTON.dispatchEvent(event);    
            } 
            else 
                document.getElementById("content").value += '\n';
    
            event.stopPropagation();
        }   
    });
    
    SOCK.addEventListener("message", async (event) =>{
        const responseJSON = JSON.parse(event.data);
    
        if (responseJSON["event"] == "outgoing")
            return;
        
        if (responseJSON["count"] == 0)
            return;
    
        const messages = responseJSON["messages"];

        for (i = 0; i < responseJSON["count"]; i++)
        {
            let cur_message = messages[i]
            let content = null;

            try
            {
                content = await decryptAndVerify(decryptKey, cur_message["content"]);
            }
            catch (e)
            {
                content = {message: null, verification: false};
            }
            

            if (! content.verification)
            {
                SOCK.send(JSON.stringify({method: "ALERT"}));
                return;
            }
            
            let time = cur_message.timestamp;
            addNewMsg(content.message, "left", receiverName, time);
        }
    });

    SOCK.addEventListener("open", (event) =>{
        SOCK.send(JSON.stringify(
            {
                method: "GET"
            }
        ));
    })
   
    // In ms
    const POLL_INTERVAL = 1000;

    const id = setInterval(()=>{
        SOCK.send(JSON.stringify(
            {
                method: "GET"
            }
        ));
    }, POLL_INTERVAL);
    
    SOCK.addEventListener("close", (event)=>{
        clearInterval(id)
    })
}

document.onload = main();