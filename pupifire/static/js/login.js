// FirebaseUI config.
const uiConfig = {
    signInSuccessUrl: "{% url 'index' %}",
    signInOptions: [
        {
            provider: firebase.auth.EmailAuthProvider.PROVIDER_ID,
            // Use email link authentication and do not require password.
            // Note this setting affects new users only.
            // For pre-existing users, they will still be prompted to provide their
            // passwords on sign-in.
            signInMethod: firebase.auth.EmailAuthProvider.EMAIL_LINK_SIGN_IN_METHOD,
            // Allow the user the ability to complete sign-in cross device, including
            // the mobile apps specified in the ActionCodeSettings object below.
            forceSameDevice: false,
            // Used to define the optional firebase.auth.ActionCodeSettings if
            // additional state needs to be passed along request and whether to open
            // the link in a mobile app if it is installed.
        },
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
    const form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = "/verify/";
    let data = {
        user: JSON.stringify(user),
        csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value
    };
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
