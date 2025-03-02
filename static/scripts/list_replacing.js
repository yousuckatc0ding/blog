
!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId captureTraceFeedback captureTraceMetric".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
posthog.init('phc_uuLYaEohY65NGpdlF7eOH2dQucCkpkP4wzs7JMsqn4v', {
    api_host: 'https://us.i.posthog.com',
    person_profiles: 'always',
})
document.addEventListener("DOMContentLoaded", function() {
    try {
        // Apply Tailwind classes to selected elements
        const elementStyles = {
            "ol, ul": ["list-disc", "pl-6"],
            p: ["my-4"],
            h1: ["text-lg"],
            pre: ["my-4"],
        };

        for (const [selector, classes] of Object.entries(elementStyles)) {
            const elements = document.querySelectorAll(selector);
            if (elements.length === 0) {
                console.log(`No ${selector} elements found on the page`);
                continue;
            }
            elements.forEach((element) => {
                element.classList.add(...classes);
            });
        }

        // Define SVG icons as strings (from Heroicons)
        const copyIcon = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
           viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 2H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V7l-6-5H9z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 2v5h6" />
      </svg>
    `;

        const checkIcon = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
           viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M5 13l4 4L19 7" />
      </svg>
    `;

        // For each code block (<pre> element), add a copy button with the clipboard icon
        document.querySelectorAll("pre").forEach((pre) => {
            // Create the copy button element
            const copyButton = document.createElement("button");
            // Use the SVG icon instead of text
            copyButton.innerHTML = copyIcon;
            // Style the button with Tailwind classes
            copyButton.classList.add(
                "inline-flex",
                "bg-blue-900",
                "text-white",
                "p-1",
                "rounded",
                "absolute",
                "top-2",
                "right-2",
                "hover:bg-blue-600",
                "focus:outline-none"
            );

            // Ensure the <pre> is relatively positioned to contain the absolute button
            pre.style.position = "relative";
            pre.appendChild(copyButton);

            // Attach the copy-to-clipboard functionality
            copyButton.addEventListener("click", async () => {
                try {
                    // If there is a <code> element, use its inner text; otherwise use the <pre>'s text.
                    const codeElement = pre.querySelector("code") || pre;
                    const codeText = codeElement.innerText;

                    // Use the Clipboard API to copy the text
                    await navigator.clipboard.writeText(codeText);

                    // Provide feedback by swapping the icon and changing button color
                    copyButton.innerHTML = checkIcon;
                    copyButton.classList.replace("bg-blue-500", "bg-green-500");

                    // Revert back after 2 seconds
                    setTimeout(() => {
                        copyButton.innerHTML = copyIcon;
                        copyButton.classList.replace("bg-green-500", "bg-blue-500");
                    }, 2000);
                } catch (err) {
                    console.error("Failed to copy code: ", err);
                }
            });
        });
    } catch (error) {
        console.error("Error while processing elements:", error);
    }
});
