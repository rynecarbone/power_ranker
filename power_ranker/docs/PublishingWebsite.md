# Publishing Power Rankings to a Website
After generating the html and css files containing your power rankings, you need
a place to host the content. Below is an example of how to create a personal 
GitHub Pages site where you can host your rankings. 

## Make a Personal GitHub Pages Site
Please refer to [GitHub Pages documentation](https://pages.github.com) for further details

### Create a repository
- Log into your GitHub, create a repository called 'username.github.io'
where 'username' is your actual username on GitHub
- If you don't have a GitHub account, [create one](https://github.com/join?source=header-home)

### Clone the repository 
- If using terminal, cd to folder where you wish to put the project
```bash
git clone https://github.com/username/username.github.io
```

- If using a desktop client, click 'Set up in Desktop' button instead

### Create an index.html
Add an index.html file (default page loaded on your site)

- If using terminal:
```bash
cd username.github.io
echo "Hello World" > index.html
```

- If using a desktop client, add a file called index.html 
to your project with the following content:
```html
<!DOCTYPE html>
<html>
<body>
<h1>Hello World</h1>
<p>I'm hosted with GitHub Pages.</p>
</body>
</html>
```

### Commit your changes

- If using terminal:
```bash
git add --all
git commit -m "Initial commit"
git push -u origin master
```

- If using a desktop client, enter the repository, commit your changes, and click sync.


### Visit your site
- Navigate to https://username.github.io on any browser


## Getting the Rankings Website on Your GitHub Pages Site
After you have run the rankings and produced the website files, you an copy them
over to your GitHub pages repository.

- Create a subdirectory to organize your site structure:
```bash
cd username.github.io
mkdir ff
```

- Copy the generated website files from the `output/` directory into your new GitHub Pages 
subdirectory. If you ran the power rankings code in the Desktop directory, for example:
```bash
cp -r ~/Desktop/output/ ff/
```

- Commit and sync your changes

- Visit your Github pages to view the rankings: https://username.github.io/ff/2017 

