CKEDITOR.addTemplates('my_templates', {
    imagesPath: CKEDITOR.getUrl('/static/img/'),  
    templates: [
        {
            title: 'Letter: Head-Office',
            image: 'template1.gif',
            description: 'Letter with header and footer',
            html: '<div class="document-header" style="position: absolute; top: 0; width: 100%;"><img src="/static/img/header.jpg" alt="Header" id="heade-img" style="width: 100%;"> <hr style="margin:0;" /></div><div class="document-body" contenteditable="true" style="margin-top: 150px; margin-bottom: 150px;"> <br/> &nbsp; <br/> &nbsp; <br/> &nbsp; <br/> &nbsp;<br/> &nbsp; <br/> &nbsp; <br/> &nbsp; <br/> &nbsp;</div><div class="document-footer" style="position: absolute; bottom: 0; width: 100%;"> <hr/> <img src="/static/img/footer.jpg" alt="Footer" style="width: 100%;"></div>',
        },
    ],
});