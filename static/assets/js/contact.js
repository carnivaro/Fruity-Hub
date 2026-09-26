const contactForm = document.getElementById("contactForm");

if(contactForm){

contactForm.addEventListener("submit", function(event){

event.preventDefault();

showToast("Thank you for contacting Fruity Hub.","success");

contactForm.reset();

});

}