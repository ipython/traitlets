# IPConfigurable

A strip down version of IPython Configuration system, 
mostly taken from IPython as is, and not yet totally cleaned. 

on particular it does not contain the configuration file loader that have some
IPython specific-ness that woudl need to be stripped. 

## Base Idea

Any object you want to be configurable should inherit from `IPConfigurable.Configurable`
and have class attributes that are instance `Trailets`.

when creating your object, pass it either the `config=` keyword (that is a
config object) or `parent=` keyword which is another `Configurable` object. 

Now any value of the form `ClassName.trait_name=Value` of the `Config` object will 
be set for the object. If you use `parent=` our can nest config in the form 
`GrandParent.Parent.Child.attribute=value`.



