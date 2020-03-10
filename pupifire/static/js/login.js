// FirebaseUI config.
const uiConfig = {
    signInSuccessUrl: "{% url 'index' %}",
    signInOptions: [
        firebase.auth.EmailAuthProvider.PROVIDER_ID,
        {
            provider: firebase.auth.PhoneAuthProvider.PROVIDER_ID,
            defaultCountry: 'AR'
        },
        firebaseui.auth.AnonymousAuthProvider.PROVIDER_ID,
    ],
    // tosUrl and privacyPolicyUrl accept either url string or a callback
    // function.
    // Terms of service url/callback.
    tosUrl: "{% url 'tos' %}",
    // Privacy policy url/callback.
    privacyPolicyUrl: function () {
        window.location.assign("{% url 'privacy-policy' %}");
    },
    'callbacks': {
        'signInSuccessWithAuthResult': function (authResult, redirectUrl) {
            if (authResult.user) {
                handleSignedInUser(authResult.user);
            }
            // Do not redirect.
            return false;
        }
    },
};

function handleSignedInUser(user){
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    const user_json = JSON.stringify(user);
    const form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = "/verify/";
    data = {user: user_json, csrfmiddlewaretoken: csrf};
    for (const name in data) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = data[name];
        form.appendChild(input);
    }
    form.submit();
}

// Initialize the FirebaseUI Widget using Firebase.
const ui = new firebaseui.auth.AuthUI(firebase.auth());
// The start method will wait until the DOM is loaded.
ui.start('#firebaseui-auth-container', uiConfig);
