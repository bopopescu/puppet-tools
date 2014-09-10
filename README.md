puppet-tools
============

Some tools to aid puppet automation

In the Puppet construction layer, we focus on writing elementary Puppet modules. So, providing the mechanism to make something work. See for a full explanation on [msat.disruptivefoss.org](http://msat.disruptivefoss.org/). Sometimes we need extra software in the Puppet construction layer, for example the stdlib Puppet Labs module. Since we run Puppet in standalone mode, we transport the software onto the target system via RPM. This gives us the task to package this *extra* software in RPM's. In this repo the extra RPM's are placed.

